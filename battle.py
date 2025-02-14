import pygame
import random
import os
import math
from typing import Dict, Optional, List
from models.pokemon import Pokemon, Move
from data_manager.file_handler import FileHandler
import numpy

class BattleSystem:
    def __init__(self, screen: pygame.Surface, pokemons: Dict):
        self.screen = screen
        self.pokemons = pokemons
        self.file_handler = FileHandler()
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.battle_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 24)
        
        # Battle state
        self.player_pokemon = None
        self.enemy_pokemon = None
        self.battle_log = []
        self.battle_state = "player_turn"
        
        # Load battle background
        self.background = pygame.Surface(screen.get_size())
        self.background.fill(self.WHITE)
        
        # Attributes for battle scene
        self.battle_backgrounds = self.load_battle_backgrounds()
        self.current_background = None
        self.animation_frame = 0
        self.animation_speed = 0.2
        self.particle_effects = []
        
        # Health bar colors and properties
        self.HP_COLORS = {
            'high': (76, 175, 80),     # Green
            'medium': (255, 152, 0),    # Orange
            'low': (244, 67, 54)        # Red
        }
        self.HP_BAR_HEIGHT = 15
        self.HP_BAR_BORDER = 2
        
        # Attack animations and effects
        self.animation_state = None
        self.animation_timer = 0

        
        # Move effects
        self.MOVE_EFFECTS = {
            'physical': {
                'color': (255, 98, 0), 
                'particles': 15,
                'speed': 8,
                'size': 5
            },
            'special': {
                'color': (0, 191, 255), 
                'particles': 20,
                'speed': 6,
                'size': 4
            },
            'status': {
                'color': (147, 112, 219), 
                'particles': 25,
                'speed': 4,
                'size': 3
            }
        }
        
        self.STATUS_EFFECTS = {
            'paralyzed': {'color': (255, 255, 0), 'chance': 0.25}, 
            'burned': {'color': (255, 69, 0), 'damage': 0.0625},
            'poisoned': {'color': (147, 112, 219), 'damage': 0.125},
            'frozen': {'color': (135, 206, 250), 'chance': 0.25},  
            'asleep': {'color': (169, 169, 169), 'turns': (2, 5)}
        }

    
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        self.sounds = self.generate_sound_effects()

    def start(self, player_data: Dict) -> Dict:
        self.player_pokemon = Pokemon.from_dict(player_data["pokemons"][0])
        self.enemy_pokemon = self.select_random_enemy()
        self.battle_log = []
        self.battle_state = "player_turn"
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return {"action": "quit"}
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return {"action": "return_to_menu"}
                    
                    if self.battle_state == "player_turn":
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                            self.handle_player_turn(event.key - pygame.K_1)
                            
                            if self.enemy_pokemon.current_hp <= 0:
                                self.handle_victory(player_data)
                                return {"action": "return_to_menu"}
                            
                            self.battle_state = "enemy_turn"
                    
                    elif self.battle_state == "enemy_turn" and event.key == pygame.K_RETURN:
                        self.handle_enemy_turn()
                        
                        if self.player_pokemon.current_hp <= 0:
                            self.handle_defeat(player_data)
                            return {"action": "return_to_menu"}
                        
                        self.battle_state = "player_turn"

            self.draw_battle()
            pygame.display.flip()

    def select_random_enemy(self) -> Pokemon:
        enemy_data = random.choice(list(self.pokemons.values()))
        return Pokemon.from_dict(enemy_data.to_dict())

    def handle_player_turn(self, move_index: int):
        move = self.player_pokemon.moves[move_index]
        
        # Check if Pokemon is paralyzed and can't move
        if self.player_pokemon.status_condition == 'paralyzed':
            if random.random() < self.STATUS_EFFECTS['paralyzed']['chance']:
                self.battle_log.append(f"{self.player_pokemon.name} is paralyzed and can't move!")
                return
        
        if move.current_pp <= 0:
            self.battle_log.append("No PP left for this move!")
            return
        
        move.current_pp -= 1
        
        damage = self.calculate_damage(self.player_pokemon, self.enemy_pokemon, move)
        self.enemy_pokemon.current_hp -= damage
        
        # Apply status effect if move has one
        if move.status_effect and random.random() < 0.8:
            self.apply_status_effect(self.enemy_pokemon, move.status_effect)
        
        self.update_status_effects(self.player_pokemon)
        
        # Add attack animation
        attacker_pos = (200, 350)  
        target_pos = (600, 200)    
        self.add_attack_particles(attacker_pos, target_pos, move)

    def calculate_damage(self, attacker: Pokemon, defender: Pokemon, move: Move) -> int:
        # Calculate damage using Pokemon game formula

        if move.category == 'status':
            return 0
            
        # Base damage formula
        level = attacker.level
        power = move.power
        
        # Attack and Defense stats
        if move.category == 'physical':
            attack = attacker.stats['attack']
            defense = defender.stats['defense']
        else:  # special
            attack = attacker.stats['special-attack']
            defense = defender.stats['special-defense']
        
        # Formula from Wikipedia article on Pokemon game
        base_damage = ((2 * level / 5 + 2) * power * attack / defense) / 50 + 2
        
        # Modifiers
        modifiers = 1.0
        
        # STAB (Same Type Attack Bonus)
        if move.type in attacker.types:
            modifiers *= 1.5
        
        # Type effectiveness
        type_effectiveness = self.calculate_type_effectiveness(move.type, defender.types)
        modifiers *= type_effectiveness
        
        # Random factor (0.85 to 1.00)
        modifiers *= random.uniform(0.85, 1.0)
        
        # Calculate final damage
        final_damage = int(base_damage * modifiers)
        
        return max(1, final_damage) # To ensure damage is at least 1. It is taken from the original Pokemon game and is used to prevent moves doing very little HP damage.

    def handle_enemy_turn(self):
        # Check if Pokemon is paralyzed and can't move
        if self.enemy_pokemon.status_condition == 'paralyzed':
            if random.random() < self.STATUS_EFFECTS['paralyzed']['chance']:
                self.battle_log.append(f"{self.enemy_pokemon.name} is paralyzed and can't move!")
                return
        
        available_moves = [m for m in self.enemy_pokemon.moves if m.current_pp > 0]
        if not available_moves:
            self.battle_log.append(f"{self.enemy_pokemon.name} has no moves left!")
            return
        
        move = random.choice(available_moves)
        move.current_pp -= 1
        
        damage = self.calculate_damage(self.enemy_pokemon, self.player_pokemon, move)
        self.player_pokemon.current_hp = max(0, self.player_pokemon.current_hp - damage)
        
        # Apply status effect if move has one
        if move.status_effect and random.random() < 0.8:
            self.apply_status_effect(self.player_pokemon, move.status_effect)
        
        # Update status effects at end of turn
        self.update_status_effects(self.enemy_pokemon)
        
        # Add attack animation
        attacker_pos = (600, 200)  
        target_pos = (200, 350)    
        self.add_attack_particles(attacker_pos, target_pos, move)

    def calculate_type_effectiveness(self, attack_type: str, defender_types: list) -> float:
        """Calculate type effectiveness multiplier"""
        # Type effectiveness chart. We use a simplified version using six types instead of 18 types in the original game
        type_chart = {
            "fire": {"grass": 2.0, "water": 0.5, "fire": 0.5},
            "water": {"fire": 2.0, "grass": 0.5, "water": 0.5},
            "grass": {"water": 2.0, "fire": 0.5, "grass": 0.5},
            "electric": {"water": 2.0, "ground": 0},
            "ground": {"electric": 2.0},
            "flying": {"ground": 0}
        }
        
        multiplier = 1.0
        for def_type in defender_types:
            if attack_type in type_chart and def_type in type_chart[attack_type]:
                multiplier *= type_chart[attack_type][def_type]
        
        return multiplier

    def handle_victory(self, player_data: Dict):
        # Increase experience of Player's Pokemon
        exp_gain = self.enemy_pokemon.level * 50
        self.player_pokemon.gain_experience(exp_gain)
        
        # Add defeated Pokemon to Player's Pokedex
        captured_pokemon = self.enemy_pokemon.to_dict()
        if captured_pokemon not in player_data["pokemons"]:
            player_data["pokemons"].append(captured_pokemon)
            self.show_message(f"Added {self.enemy_pokemon.name.capitalize()} to your Pokedex!")
        
        # Check for evolution
        if self.player_pokemon.can_evolve():
            self.show_evolution_animation()
            self.player_pokemon.evolve()
        
        # Update Player's Pokedex
        player_data["pokemons"][0] = self.player_pokemon.to_dict()
        self.file_handler.save_pokedex(player_data["name"], player_data)
        
        self.show_message(f"You won! Gained {exp_gain} experience!")

    def handle_defeat(self, player_data: Dict):
        # Remove defeated Pokemon from Pokedex
        defeated_pokemon = self.player_pokemon.to_dict()
        player_data["pokemons"].remove(defeated_pokemon)
        self.file_handler.save_pokedex(player_data["name"], player_data)
        
        self.show_message(f"{self.player_pokemon.name.capitalize()} has been removed from your Pokedex!")
        self.show_message("You lost! Better luck next time!")

    def draw_battle(self):
        self.screen.fill(self.WHITE)
        
        # Draw battle background if available
        if not self.current_background:
            # Select background based on Pokemon types
            bg_type = self.select_background_type()
            if bg_type in self.battle_backgrounds:
                self.current_background = self.battle_backgrounds[bg_type]
        
        if self.current_background:
            self.screen.blit(self.current_background, (0, 0))
        
        # Draw Pokemon sprites and animations
        self.draw_animated_pokemon()

        self.update()
        self.update_and_draw_particles()
        
        # Draw attack animations if active
        if self.animation_state:
            self.draw_attack_animation()
        
        # Draw HP bars
        self.draw_health_bar(self.enemy_pokemon, (450, 100), False)
        self.draw_health_bar(self.player_pokemon, (50, 300), True)

        self.draw_status_effects()
        
        # Draw battle log with fade effect
        self.draw_battle_log_with_fade()

    def draw_health_bar(self, pokemon: Pokemon, position: tuple, is_player: bool):

        x, y = position
        max_hp = pokemon.stats["hp"]
        current_hp = pokemon.current_hp
        hp_percentage = current_hp / max_hp
        
        if hp_percentage > 0.5:
            color = self.HP_COLORS['high']
        elif hp_percentage > 0.25:
            color = self.HP_COLORS['medium']
        else:
            color = self.HP_COLORS['low']
        
        name_plate = pygame.Surface((270, 80))
        name_plate.set_alpha(200)
        name_plate.fill((40, 40, 40))
        self.screen.blit(name_plate, (x - 10, y - 10))
        
        name_font = pygame.font.Font(None, 32)
        self.draw_text(f"{pokemon.name.capitalize()} Lv.{pokemon.level}",
                      (x, y), name_font, self.WHITE)
        
        bar_bg = pygame.Rect(x, y + 30, 220, self.HP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, (40, 40, 40), bar_bg)
        
        bar_width = int(220 * hp_percentage)
        bar_rect = pygame.Rect(x, y + 30, bar_width, self.HP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, color, bar_rect)
        
        pygame.draw.rect(self.screen, self.WHITE, bar_bg, self.HP_BAR_BORDER)
        
        hp_font = pygame.font.Font(None, 20)
        hp_text = f"{current_hp}/{max_hp}"
        self.draw_text(hp_text, (x + 230, y + 30),
                      hp_font, self.WHITE)

    def draw_animated_pokemon(self):
        if not self.animation_state:
            # Add idle animation when no attack is happening
            idle_offset = math.sin(pygame.time.get_ticks() * 0.005) * 3  # Smooth up/down movement
            
            player_pos = (200, 350 + idle_offset)  
            enemy_pos = (600, 200 + idle_offset)
            
            # Draw the Pokemon
            flipped_sprite = pygame.transform.flip(self.player_pokemon.sprite, True, False)
            self.screen.blit(flipped_sprite, player_pos)
            self.screen.blit(self.enemy_pokemon.sprite, enemy_pos)
            return

        # Animation for attacks
        shake_offset = self.animation_state.get('shake_offset', 0)
        is_flashing = self.animation_state.get('flash', False)
        
        if self.animation_state['source'] == 'player':
            # Player is attacking, so enemy shakes
            player_pos = (200, 350)
            enemy_pos = (600 + shake_offset, 200)
            
            # Draw player normally
            flipped_sprite = pygame.transform.flip(self.player_pokemon.sprite, True, False)
            self.screen.blit(flipped_sprite, player_pos)
            
            # Draw enemy with potential flash effect
            if is_flashing:
                sprite = self.enemy_pokemon.sprite.copy()
                white_overlay = pygame.Surface(sprite.get_size())
                white_overlay.fill((255, 255, 255))
                sprite.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_ADD)
                self.screen.blit(sprite, enemy_pos)
            else:
                self.screen.blit(self.enemy_pokemon.sprite, enemy_pos)
        else:
            # Enemy is attacking, so player shakes
            player_pos = (200 + shake_offset, 350)
            enemy_pos = (600, 200)
            
            # Draw enemy normally
            self.screen.blit(self.enemy_pokemon.sprite, enemy_pos)
            
            # Draw player with potential flash effect
            if is_flashing:
                sprite = pygame.transform.flip(self.player_pokemon.sprite, True, False)
                white_overlay = pygame.Surface(sprite.get_size())
                white_overlay.fill((255, 255, 255))
                sprite.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_ADD)
                self.screen.blit(sprite, player_pos)
            else:
                flipped_sprite = pygame.transform.flip(self.player_pokemon.sprite, True, False)
                self.screen.blit(flipped_sprite, player_pos)

    def add_attack_particles(self, attacker_pos: tuple, target_pos: tuple, move: Move):
    
        if not self.animation_state:
            
            dx = target_pos[0] - attacker_pos[0]
            dy = target_pos[1] - attacker_pos[1]
            distance = math.sqrt(dx*dx + dy*dy)
            dir_x = dx/distance if distance > 0 else 0
            dir_y = dy/distance if distance > 0 else 0
            
            self.animation_state = {
                'type': 'attack',
                'particles': [],
                'timer': 0,
                'move': move,
                'source': 'player' if attacker_pos[0] < target_pos[0] else 'enemy',
                'start_pos': attacker_pos,
                'end_pos': target_pos,
                'direction': (dir_x, dir_y)
            }
            
            num_particles = 40  
            
            if move.type == 'fire':
            
                for _ in range(num_particles):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(6, 12)
                    particle = {
                        'pos': list(attacker_pos),
                        'vel': [speed * math.cos(angle), speed * math.sin(angle)],
                        'life': 1.0,
                        'size': random.uniform(6, 14),
                        'color': (255, random.randint(50, 150), 0),
                        'type': 'flame',
                        'angle': random.uniform(0, 360),
                        'flicker': random.uniform(0.8, 1.2)  # Flame flicker rate
                    }
                    self.animation_state['particles'].append(particle)
                    
                    # Add spark particle
                    if random.random() < 0.5:  # 50% chance for each flame
                        spark = {
                            'pos': list(attacker_pos),
                            'vel': [speed * 1.5 * math.cos(angle), speed * 1.5 * math.sin(angle)],
                            'life': 0.8,
                            'size': random.uniform(2, 4),
                            'color': (255, 255, random.randint(100, 200)),
                            'type': 'spark'
                        }
                        self.animation_state['particles'].append(spark)
                
            elif move.type == 'water':
                for _ in range(num_particles):
                    particle = {
                        'pos': list(attacker_pos),
                        'vel': [dir_x * random.uniform(8, 14) + random.uniform(-2, 2),
                               dir_y * random.uniform(8, 14) + random.uniform(-2, 2)],
                        'life': 1.0,
                        'size': random.uniform(4, 8),
                        'color': (0, random.randint(150, 255), 255),
                        'type': 'droplet',
                        'trail': [],
                        'splash_created': False  
                    }
                    self.animation_state['particles'].append(particle)
                
            elif move.type == 'electric':
                for _ in range(num_particles):
                    particle = {
                        'pos': list(attacker_pos),
                        'vel': [dir_x * random.uniform(12, 18) + random.uniform(-3, 3),
                               dir_y * random.uniform(12, 18) + random.uniform(-3, 3)],
                        'life': 1.0,
                        'size': random.uniform(3, 6),
                        'color': (255, 255, random.randint(0, 50)),
                        'type': 'lightning',
                        'branches': [],
                        'arc_timer': 0,  
                        'intensity': random.uniform(0.8, 1.2) 
                    }
                    self.animation_state['particles'].append(particle)
                
            elif move.type == 'grass':
                for _ in range(num_particles):
                    particle = {
                        'pos': list(attacker_pos),
                        'vel': [dir_x * random.uniform(6, 10) + random.uniform(-2, 2),
                               dir_y * random.uniform(6, 10) + random.uniform(-2, 2)],
                        'life': 1.0,
                        'size': random.uniform(6, 12),
                        'color': (random.randint(50, 100), 255, random.randint(0, 50)),
                        'type': 'leaf',
                        'angle': random.uniform(0, 360),
                        'spin': random.uniform(-5, 5),
                        'swirl_offset': random.uniform(0, math.pi * 2)  # For swirling motion
                    }
                    self.animation_state['particles'].append(particle)
                    
                    
                    if random.random() < 0.3: 
                        pollen = {
                            'pos': list(attacker_pos),
                            'vel': [dir_x * random.uniform(3, 6), dir_y * random.uniform(3, 6)],
                            'life': 1.2,
                            'size': random.uniform(1, 3),
                            'color': (255, 255, 150),
                            'type': 'pollen',
                            'swirl_offset': random.uniform(0, math.pi * 2)
                        }
                        self.animation_state['particles'].append(pollen)
            
            else: 
                for _ in range(num_particles):
                    particle = {
                        'pos': list(attacker_pos),
                        'vel': [dir_x * random.uniform(8, 12) + random.uniform(-2, 2),
                               dir_y * random.uniform(8, 12) + random.uniform(-2, 2)],
                        'life': 1.0,
                        'size': random.uniform(4, 8),
                        'color': (255, 255, 255),
                        'type': 'normal',
                        'angle': random.uniform(0, 360)
                    }
                    self.animation_state['particles'].append(particle)

    def update_and_draw_particles(self):
        if not self.animation_state:
            return
        
        move = self.animation_state['move']
        
        
        for particle in self.animation_state['particles']:
            prev_pos = list(particle['pos'])
            
        
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            
            
            if particle['type'] == 'flame':
                particle['angle'] += random.uniform(-10, 10)
                particle['size'] = max(2, particle['size'] - 0.2)
                particle['vel'][1] -= 0.3  
                
            elif particle['type'] == 'droplet':
                particle['vel'][1] += 0.3  
                if len(particle.get('trail', [])) > 5:
                    particle['trail'].pop(0)
                particle['trail'].append(list(particle['pos']))
                
            elif particle['type'] == 'lightning':
                particle['pos'][0] += math.sin(self.animation_timer * 1.2) * 5
                if random.random() < 0.1:  
                    particle['branches'].append({
                        'start': list(particle['pos']),
                        'angle': random.uniform(0, 360),
                        'length': random.uniform(5, 15)
                    })
                
            elif particle['type'] == 'leaf':
                particle['angle'] += particle['spin']
                particle['vel'][1] += math.sin(self.animation_timer * 0.5) * 0.1
                
            
            particle['vel'][0] += random.uniform(-0.2, 0.2)
            particle['vel'][1] += random.uniform(-0.2, 0.2)
            
            
            particle['life'] -= 0.015
        
    
        self.animation_state['particles'] = [p for p in self.animation_state['particles'] 
                                           if p['life'] > 0]
        
        
        for particle in self.animation_state['particles']:
            alpha = max(0, min(255, int(particle['life'] * 255)))
            color = particle['color']
            pos = [int(particle['pos'][0]), int(particle['pos'][1])]
            
            try:
                if particle['type'] == 'flame':
                    # Draw flame shape
                    points = []
                    size = particle['size']
                    for i in range(3):
                        angle = math.radians(particle['angle'] + i * 120)
                        points.append((
                            pos[0] + math.cos(angle) * size,
                            pos[1] + math.sin(angle) * size
                        ))
                    glow_color = (*color[:3], alpha)
                    pygame.draw.polygon(self.screen, glow_color, points)
                    
                elif particle['type'] == 'droplet':
                    for trail_pos in particle.get('trail', []):
                        trail_alpha = int(alpha * 0.3)
                        trail_color = (*color[:3], trail_alpha)
                        pygame.draw.circle(self.screen, trail_color, 
                                        [int(trail_pos[0]), int(trail_pos[1])], 
                                        int(particle['size'] * 0.5))
                    drop_color = (*color[:3], alpha)
                    pygame.draw.circle(self.screen, drop_color, pos, int(particle['size']))
                    
                elif particle['type'] == 'lightning':
                    for branch in particle.get('branches', []):
                        end_pos = (pos[0] + math.cos(math.radians(branch['angle'])) * branch['length'],
                          pos[1] + math.sin(math.radians(branch['angle'])) * branch['length'])
                        branch_color = (*color[:3], int(alpha * 0.7))
                        pygame.draw.line(self.screen, branch_color, 
                                       branch['start'], [end_pos[0], end_pos[1]], 2)
                    main_color = (*color[:3], alpha)
                    pygame.draw.circle(self.screen, main_color, pos, int(particle['size']))
                    
                elif particle['type'] == 'leaf':
                    leaf_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
                    leaf_color = (*color[:3], alpha)
                    points = [
                        (10, 0), (15, 5), (15, 15), (10, 20), (5, 15), (5, 5)
                    ]
                    pygame.draw.polygon(leaf_surface, leaf_color, points)
                    rotated = pygame.transform.rotate(leaf_surface, particle['angle'])
                    self.screen.blit(rotated, (pos[0] - rotated.get_width()/2,
                                             pos[1] - rotated.get_height()/2))
                    
                elif particle['type'] == 'spark':
                    spark_color = (*color[:3], alpha)
                    pygame.draw.circle(self.screen, spark_color, pos, int(particle['size']))
                    
                elif particle['type'] == 'pollen':
                    pollen_color = (*color[:3], int(alpha * 0.7))
                    pygame.draw.circle(self.screen, pollen_color, pos, int(particle['size'] * 1.5))
                    
                else: 
                    glow_color = (*color[:3], int(alpha * 0.6))
                    pygame.draw.circle(self.screen, glow_color, pos, 
                                     int(particle['size'] * 1.5))
                    main_color = (*color[:3], alpha)
                    pygame.draw.circle(self.screen, main_color, pos, 
                                     int(particle['size']))
                
            except (TypeError, ValueError, IndexError) as e:
                pygame.draw.circle(self.screen, (255, 255, 255, alpha), pos, int(particle['size']))
        
        if not self.animation_state['particles']:
            self.animation_state = None

    def draw_battle_log_with_fade(self):
        log_surface = pygame.Surface((600, 100))
        log_surface.set_alpha(200)
        log_surface.fill((40, 40, 40))
        
        y = 10
        for i, message in enumerate(self.battle_log[-3:]):
            alpha = 255 - (i * 50) 
            text_surface = self.info_font.render(message, True, self.WHITE)
            text_surface.set_alpha(alpha)
            log_surface.blit(text_surface, (10, y))
            y += 30
            
        self.screen.blit(log_surface, (100, 500))

    def draw_text(self, text: str, position: tuple, font: pygame.font.Font, 
                 color: tuple = None, center: bool = False):
        if color is None:
            color = self.BLACK
        text_surface = font.render(text, True, color)
        if center:
            text_rect = text_surface.get_rect(center=position)
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, position)

    def show_message(self, message: str, duration: int = 2000):
        self.screen.fill(self.WHITE)
        self.draw_text(message, (400, 300), self.battle_font, center=True)
        pygame.display.flip()
        pygame.time.wait(duration)

    def show_evolution_animation(self):
        original_sprite = self.player_pokemon.sprite
        
        # Evolution animation
        for _ in range(3):  # Flash 3 times
            # Flash white
            self.screen.fill(self.WHITE)
            sprite_rect = original_sprite.get_rect(center=(400, 300))
            self.screen.blit(original_sprite, sprite_rect)
            pygame.display.flip()
            pygame.time.wait(200)
            
            # Flash blue
            self.screen.fill(self.BLUE)
            self.draw_text("Evolving...", (400, 300), self.title_font, center=True)
            pygame.display.flip()
            pygame.time.wait(200)

    def load_battle_backgrounds(self):
        backgrounds = {}
        background_types = ['grass', 'water', 'cave', 'gym']
        
        for bg_type in background_types:
            try:
                path = os.path.join('images', 'battles', f'{bg_type}.png')
                bg = pygame.image.load(path)
                backgrounds[bg_type] = pygame.transform.scale(bg, self.screen.get_size())
            except Exception as e:
                print(f"Error loading {bg_type} background: {e}")
                
        return backgrounds

    def select_background_type(self) -> str:
        # Get types from both Pokemon
        enemy_type = self.enemy_pokemon.types[0].lower()
        player_type = self.player_pokemon.types[0].lower()
        
        # Map Pokemon types to background types
        type_to_background = {
            'grass': 'grass',
            'water': 'water',
            'ground': 'cave',
            'rock': 'cave',
            'fighting': 'gym',
            'normal': 'gym'
        }
        
        # Try to select background based on enemy Pokemon's type first
        bg_type = type_to_background.get(enemy_type)
        if bg_type:
            return bg_type
        
        # If no match, try player Pokemon's type
        bg_type = type_to_background.get(player_type)
        if bg_type:
            return bg_type
        
        # Default to gym background if no matching type
        return 'gym'

    def update_battle_animations(self):
        if not self.animation_state:
            return
            
        self.animation_timer += 1
        
        if self.animation_state['type'] == 'attack':
            self.update_attack_animation()
        elif self.animation_state['type'] == 'status':
            self.update_status_animation()

    def update_attack_animation(self):
        if not self.animation_state:
            return
            
        anim = self.animation_state
        anim['animation_timer'] = anim.get('animation_timer', 0) + 1
        
        
        # Add flash effect and create impact particles right when hit
        if anim['animation_timer'] == 90:  
            anim['flash'] = True
            target_pos = (600, 200) if anim['source'] == 'player' else (200, 350)
            self.create_impact_effect(target_pos, anim['move'].type)
        elif 60 < anim['animation_timer'] <= 65:  
            anim['flash'] = True
        else:
            anim['flash'] = False
        
        if 60 <= anim['animation_timer'] <= 360:
            anim['shake_offset'] = 10 if anim['animation_timer'] % 2 == 0 else -10
            print(f"Shaking! Offset: {anim['shake_offset']}")
        else:
            anim['shake_offset'] = 0
        
        for particle in anim['particles']:
            particle['pos'][0] += particle['vel'][0] * 0.175
            particle['pos'][1] += particle['vel'][1] * 0.175
            particle['life'] -= 0.0035
        
        # Remove dead particles
        anim['particles'] = [p for p in anim['particles'] if p['life'] > 0]
        
        print(f"Number of particles: {len(anim['particles'])}")
        print(f"Shake offset: {anim.get('shake_offset', 0)}")
        
        if not anim['particles'] and anim['animation_timer'] > 360:
            print("Animation ended - no particles left")
            self.animation_state = None

    def create_impact_effect(self, pos, move_type):
        # Play sound effect
        move_sound = self.sounds.get(move_type.lower(), self.sounds.get('normal'))
        if move_sound:
            move_sound.play()
        

    def draw_attack_animation(self):
        if not self.animation_state:
            return
        
        for particle in self.animation_state['particles']:
            if particle['type'] == 'impact':
                pos = [int(particle['pos'][0]), int(particle['pos'][1])]
                
                pulse = math.sin(self.animation_state['animation_timer'] * particle['pulse_rate'])
                current_size = particle['original_size'] + (pulse * 2)  # Size varies by ±2 pixels
                size = int(current_size)
                
                glow_size = size * 2
                glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                glow_color = particle['glow_color']
                pygame.draw.circle(glow_surface, glow_color, 
                                 (glow_size, glow_size), glow_size)
                
                alpha = int(particle['life'] * 255)
                glow_surface.set_alpha(alpha)
                
                self.screen.blit(glow_surface, 
                               (pos[0] - glow_size, pos[1] - glow_size))
                
                color = particle['color']
                pygame.draw.circle(self.screen, (*color, alpha), pos, size)
                
                core_size = max(1, size // 3)
                pygame.draw.circle(self.screen, (255, 255, 255, alpha), 
                                 pos, core_size)

    def draw_status_effects(self):
        # Status abbreviations dictionary
        STATUS_ABBREV = {
            'paralyzed': 'PLZ',
            'burned': 'BRN',
            'poisoned': 'PSN',
            'frozen': 'FRZ',
            'asleep': 'SLP'
        }
        
        if self.player_pokemon.status_condition:
            effect = self.STATUS_EFFECTS[self.player_pokemon.status_condition]
            status_color = effect['color']
            
            # Create smaller status indicator surface
            status_indicator = pygame.Surface((20, 8))
            status_indicator.fill(status_color)
            
            # Position it in upper right corner of HP box
            player_pos = (50, 300)
            self.screen.blit(status_indicator, (player_pos[0] + 200, player_pos[1] - 5))
            
            # Draw abbreviated status name
            status_text = self.info_font.render(
                STATUS_ABBREV[self.player_pokemon.status_condition],
                True,
                self.WHITE
            )
            self.screen.blit(status_text, (player_pos[0] + 200, player_pos[1] + 5))
        
        # Draw status indicator for enemy Pokemon
        if self.enemy_pokemon.status_condition:
            effect = self.STATUS_EFFECTS[self.enemy_pokemon.status_condition]
            status_color = effect['color']
            
            status_indicator = pygame.Surface((20, 8))
            status_indicator.fill(status_color)
            enemy_pos = (450, 100)
            self.screen.blit(status_indicator, (enemy_pos[0] + 200, enemy_pos[1] - 5))
            status_text = self.info_font.render(
                STATUS_ABBREV[self.enemy_pokemon.status_condition],
                True,
                self.WHITE
            )
            self.screen.blit(status_text, (enemy_pos[0] + 200, enemy_pos[1] + 5))

    def check_move_hits(self, attacker: Pokemon, defender: Pokemon, move: Move) -> bool:
        if move.accuracy == 0:  
            return True
        
        accuracy = move.accuracy
        
        return random.uniform(0, 100) <= accuracy

    def modify_stat(self, pokemon: Pokemon, stat: str, stages: int):
        if stat not in pokemon.stat_stages:
            pokemon.stat_stages[stat] = 0
        
        pokemon.stat_stages[stat] = max(-6, min(6, pokemon.stat_stages[stat] + stages))
        
        if pokemon.stat_stages[stat] >= 0:
            modifier = (2 + pokemon.stat_stages[stat]) / 2
        else:
            modifier = 2 / (2 - pokemon.stat_stages[stat])
        
        
        base_stat = pokemon.stats[stat]
        pokemon.current_stats[stat] = int(base_stat * modifier)

        if stages > 0:
            message = f"{pokemon.name}'s {stat} rose!"
        else:
            message = f"{pokemon.name}'s {stat} fell!"
        self.battle_log.append(message)

    def get_type_color(self, attack_type: str) -> tuple:
        type_colors = {
            'normal': (168, 168, 120),    # Beige
            'fire': (240, 128, 48),       # Orange-red
            'water': (104, 144, 240),     # Blue
            'electric': (248, 208, 48),   # Yellow
            'grass': (120, 200, 80),      # Green
            'ice': (152, 216, 216),       # Light blue
            'fighting': (192, 48, 40),    # Dark red
            'poison': (160, 64, 160),     # Purple
            'ground': (224, 192, 104),    # Brown
            'flying': (168, 144, 240),    # Light purple
            'psychic': (248, 88, 136),    # Pink
            'bug': (168, 184, 32),        # Light green
            'rock': (184, 160, 56),       # Dark brown
            'ghost': (112, 88, 152),      # Dark purple
            'dragon': (112, 56, 248),     # Dark blue
            'dark': (112, 88, 72),        # Dark gray
            'steel': (184, 184, 208),     # Silver
            'fairy': (238, 153, 172)      # Light pink
        }
        
        return type_colors.get(attack_type.lower(), (128, 128, 128))

    def apply_status_effect(self, pokemon: Pokemon, status: str):
        if status not in self.STATUS_EFFECTS:
            return
        
        if pokemon.status_condition:
            self.battle_log.append(f"{pokemon.name} already has a status condition!")
            return
        
        pokemon.status_condition = status
        self.battle_log.append(f"{pokemon.name} was {status}!")

    def update_status_effects(self, pokemon: Pokemon):
        if not pokemon.status_condition:
            return
        
        effect = self.STATUS_EFFECTS[pokemon.status_condition]
        
        if pokemon.status_condition == 'burned':
            damage = int(pokemon.stats['hp'] * effect['damage'])
            pokemon.current_hp = max(0, pokemon.current_hp - damage)
            self.battle_log.append(f"{pokemon.name} was hurt by its burn!")
        
        elif pokemon.status_condition == 'poisoned':
            damage = int(pokemon.stats['hp'] * effect['damage'])
            pokemon.current_hp = max(0, pokemon.current_hp - damage)
            self.battle_log.append(f"{pokemon.name} was hurt by poison!")
        
        elif pokemon.status_condition == 'asleep':
            if not hasattr(pokemon, 'sleep_turns'):
                pokemon.sleep_turns = random.randint(*effect['turns'])
            
            pokemon.sleep_turns -= 1
            if pokemon.sleep_turns <= 0:
                pokemon.status_condition = None
                self.battle_log.append(f"{pokemon.name} woke up!")
            else:
                self.battle_log.append(f"{pokemon.name} is fast asleep!")

    def draw_modern_health_bar(self, pokemon: Pokemon, position: tuple, is_player: bool):
        x, y = position
        max_hp = pokemon.stats["hp"]
        current_hp = pokemon.current_hp
        hp_percentage = current_hp / max_hp
        
        if hp_percentage > 0.5:
            color = self.HP_COLORS['high']
        elif hp_percentage > 0.25:
            color = self.HP_COLORS['medium']
        else:
            color = self.HP_COLORS['low']
        
        name_plate = pygame.Surface((270, 80))
        name_plate.set_alpha(200)
        name_plate.fill((40, 40, 40))
        self.screen.blit(name_plate, (x - 10, y - 10))
        
        name_font = pygame.font.Font(None, 32)
        self.draw_text(f"{pokemon.name.capitalize()} Lv.{pokemon.level}",
                      (x, y), name_font, self.WHITE)
        
        bar_bg = pygame.Rect(x, y + 30, 220, self.HP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, (40, 40, 40), bar_bg)
        
        bar_width = int(220 * hp_percentage)
        bar_rect = pygame.Rect(x, y + 30, bar_width, self.HP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, color, bar_rect)
        
        pygame.draw.rect(self.screen, self.WHITE, bar_bg, self.HP_BAR_BORDER)
        
        hp_font = pygame.font.Font(None, 20)
        hp_text = f"{current_hp}/{max_hp}"
        self.draw_text(hp_text, (x + 230, y + 30),
                      hp_font, self.WHITE)
        
        if pokemon.status_condition:
            status_color = self.STATUS_EFFECTS[pokemon.status_condition]['color']
            status_indicator = pygame.Surface((15, 15))
            status_indicator.fill(status_color)
            self.screen.blit(status_indicator, (x + 250, y + 5))

    def draw_pokemon_flash(self, pokemon, position):
    
        sprite = pokemon.back_sprite if hasattr(pokemon, 'back_sprite') else pokemon.sprite
        
        flash_sprite = sprite.copy()
        
        # Create a white overlay
        white_overlay = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
        white_overlay.fill((255, 255, 255, 128))  # Semi-transparent white
        
        # Apply the white overlay
        flash_sprite.blit(white_overlay, (0, 0))
        
        # Draw the flashing sprite
        self.screen.blit(flash_sprite, position)

    def create_attack_particles(self, attacker_pos, move_type):
        
        # Adjust source positions to be closer to the Pokémon sprites
        if attacker_pos[0] < 400:  # Player
            source_pos = (250, 350)
        else:  # Enemy
            source_pos = (550, 200)
        
        if not self.animation_state:
            self.animation_state = {
                'type': 'attack',
                'particles': [],
                'move': move_type,
                'source': 'player' if attacker_pos[0] < 400 else 'enemy',
                'impact': False,
                'impact_duration': 0,
                'animation_timer': 0  # Add animation timer to state
            }
        
        target_pos = (550, 200) if attacker_pos[0] < 400 else (250, 350)
        dx = target_pos[0] - source_pos[0]
        dy = target_pos[1] - source_pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            dir_x = dx/dist
            dir_y = dy/dist
        else:
            dir_x = dir_y = 0

        num_particles = 20
        
        base_particle = {
            'pos': list(source_pos),
            'life': 1.0,
            'sparkle': 0,  # Add default sparkle value
            'rotation': 0,  # Add default rotation
            'flicker': 1.0,  # Add default flicker
            'trail': [],    # Add default trail
            'shimmer': 1.0, # Add default shimmer
            'intensity': 1.0 # Add default intensity
        }
        
        if move_type == 'fire':
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(8, 12)
                particle = base_particle.copy()
                particle.update({
                    'vel': [speed * math.cos(angle) + dir_x * 8, 
                           speed * math.sin(angle) + dir_y * 8],
                    'size': random.uniform(4, 8),
                    'color': (255, random.randint(100, 200), 0),
                    'type': 'flame',
                    'flicker': random.uniform(0.8, 1.2),
                    'rotation': random.uniform(0, 360)
                })
                self.animation_state['particles'].append(particle)
        
        elif move_type == 'water':
            for _ in range(num_particles):
                particle = base_particle.copy()
                particle.update({
                    'vel': [dir_x * random.uniform(8, 12) + random.uniform(-2, 2),
                           dir_y * random.uniform(8, 12) + random.uniform(-2, 2)],
                    'size': random.uniform(3, 6),
                    'color': (0, random.randint(150, 255), 255),
                    'type': 'water',
                    'trail': [],
                    'shimmer': random.uniform(0.7, 1.0)
                })
                self.animation_state['particles'].append(particle)
        
        elif move_type == 'electric':
            for _ in range(num_particles):
                particle = base_particle.copy()
                particle.update({
                    'vel': [dir_x * random.uniform(10, 15) + random.uniform(-3, 3),
                           dir_y * random.uniform(10, 15) + random.uniform(-3, 3)],
                    'size': random.uniform(2, 4),
                    'color': (255, 255, random.randint(0, 100)),
                    'type': 'electric',
                    'intensity': random.uniform(0.8, 1.2)
                })
                self.animation_state['particles'].append(particle)
        
        else: 
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(8, 12)
                particle = base_particle.copy()
                particle.update({
                    'vel': [speed * math.cos(angle) + dir_x * 6,
                           speed * math.sin(angle) + dir_y * 6],
                    'size': random.uniform(3, 6),
                    'color': (255, 255, 255),
                    'type': 'normal',
                    'sparkle': random.uniform(0, 2 * math.pi)
                })
                self.animation_state['particles'].append(particle)

    def update(self):
        self.update_attack_animation()
        
        self.update_battle_animations()

    def generate_sound_effects(self):

        sounds = {}
        
        try:
            sample_rate = 44100
            amplitude = 32767
            
            # Normal hit (punchy impact with echo)
            duration = 0.15
            samples = int(duration * sample_rate)
            buffer = numpy.zeros((samples, 2), dtype=numpy.int16)
            t = numpy.linspace(0, duration, samples)
            
            waveform = amplitude * (numpy.exp(-t * 40) * numpy.sin(2 * numpy.pi * 440 * t) +
                                  numpy.exp(-t * 20) * numpy.sin(2 * numpy.pi * 220 * t) * 0.5)
            buffer[:, 0] = waveform
            buffer[:, 1] = waveform
            sounds['normal'] = pygame.sndarray.make_sound(buffer)
            
            # Fire 
            duration = 0.3
            samples = int(duration * sample_rate)
            buffer = numpy.zeros((samples, 2), dtype=numpy.int16)
            t = numpy.linspace(0, duration, samples)
            freq = numpy.linspace(150, 400, samples)
            noise = numpy.random.rand(samples)
            waveform = amplitude * (
                numpy.exp(-t * 10) * numpy.sin(2 * numpy.pi * freq * t) * 0.7 +
                numpy.exp(-t * 5) * noise * 0.3
            )
            buffer[:, 0] = waveform
            buffer[:, 1] = waveform
            sounds['fire'] = pygame.sndarray.make_sound(buffer)
            
            duration = 0.2
            samples = int(duration * sample_rate)
            buffer = numpy.zeros((samples, 2), dtype=numpy.int16)
            t = numpy.linspace(0, duration, samples)
            # Oscillating high frequency
            freq_mod = numpy.sin(2 * numpy.pi * 50 * t) * 200 + 800
            waveform = amplitude * numpy.exp(-t * 15) * numpy.sin(2 * numpy.pi * freq_mod * t)
            buffer[:, 0] = waveform
            buffer[:, 1] = waveform
            sounds['electric'] = pygame.sndarray.make_sound(buffer)
            
            # Water
            duration = 0.25
            samples = int(duration * sample_rate)
            buffer = numpy.zeros((samples, 2), dtype=numpy.int16)
            t = numpy.linspace(0, duration, samples)
            bubble_freq = 300 + numpy.sin(2 * numpy.pi * 20 * t) * 100
            waveform = amplitude * (
                numpy.exp(-t * 20) * numpy.sin(2 * numpy.pi * 150 * t) * 0.6 +
                numpy.exp(-t * 10) * numpy.sin(2 * numpy.pi * bubble_freq * t) * 0.4
            )
            buffer[:, 0] = waveform
            buffer[:, 1] = waveform
            sounds['water'] = pygame.sndarray.make_sound(buffer)
            
            duration = 0.2
            samples = int(duration * sample_rate)
            buffer = numpy.zeros((samples, 2), dtype=numpy.int16)
            t = numpy.linspace(0, duration, samples)
            freq = numpy.exp(-t * 10) * 400 + 100
            waveform = amplitude * numpy.exp(-t * 15) * numpy.sin(2 * numpy.pi * freq * t)
            buffer[:, 0] = waveform
            buffer[:, 1] = waveform
            sounds['grass'] = pygame.sndarray.make_sound(buffer)
            
            # Critical hit
            duration = 0.3
            samples = int(duration * sample_rate)
            buffer = numpy.zeros((samples, 2), dtype=numpy.int16)
            t = numpy.linspace(0, duration, samples)
            waveform = amplitude * (
                numpy.exp(-t * 30) * numpy.sin(2 * numpy.pi * 200 * t) +
                numpy.exp(-t * 20) * numpy.sin(2 * numpy.pi * 400 * t) * 0.7 +
                numpy.exp(-t * 10) * numpy.sin(2 * numpy.pi * 600 * t) * 0.4
            )
            buffer[:, 0] = waveform
            buffer[:, 1] = waveform
            sounds['critical'] = pygame.sndarray.make_sound(buffer)
            
            volumes = {
                'normal': 0.7,
                'fire': 0.8,
                'electric': 0.6,
                'water': 0.7,
                'grass': 0.75,
                'critical': 0.9
            }
            
            for sound_type, sound in sounds.items():
                sound.set_volume(volumes.get(sound_type, 0.7))
            
        except Exception as e:
            print(f"Error generating sounds: {e}")
            # Create silent fallback sounds
            buffer = numpy.zeros((1000, 2), dtype=numpy.int16)
            for key in ['normal', 'fire', 'electric', 'water', 'grass', 'critical']:
                sounds[key] = pygame.sndarray.make_sound(buffer)
        
        return sounds

def start_battle(screen, player_pokemon, enemy_pokemon):
    battle = BattleSystem(screen, player_pokemon, enemy_pokemon)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if battle.handle_input(event):
                continue
        
        battle.update()
        battle.draw_battle()
        pygame.display.flip()
        
        if battle.battle_state == 'end':
            running = False
    
    return battle.player_pokemon.current_hp > 0