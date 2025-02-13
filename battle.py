import pygame
import random
import os
import math
from typing import Dict, Optional, List
from models.pokemon import Pokemon, Move
from data_manager.file_handler import FileHandler

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
        self.attack_sprites = self.load_attack_sprites()
        
        # Move effects
        self.MOVE_EFFECTS = {
            'physical': {
                'color': (255, 98, 0),  # Orange
                'particles': 15,
                'speed': 8,
                'size': 5
            },
            'special': {
                'color': (0, 191, 255),  # Deep sky blue
                'particles': 20,
                'speed': 6,
                'size': 4
            },
            'status': {
                'color': (147, 112, 219),  # Purple
                'particles': 25,
                'speed': 4,
                'size': 3
            }
        }
        
        # Status conditions
        self.STATUS_EFFECTS = {
            'paralyzed': {'color': (255, 255, 0), 'chance': 0.25},  # Yellow
            'burned': {'color': (255, 69, 0), 'damage': 0.0625},    # Red-orange
            'poisoned': {'color': (147, 112, 219), 'damage': 0.125},# Purple
            'frozen': {'color': (135, 206, 250), 'chance': 0.25},   # Light blue
            'asleep': {'color': (169, 169, 169), 'turns': (2, 5)}   # Gray
        }

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
        
        if move.current_pp <= 0:
            self.battle_log.append("No PP left for this move!")
            return
        
        move.current_pp -= 1
        
        # Check if move hits
        if not self.check_move_hits(self.player_pokemon, self.enemy_pokemon, move):
            self.battle_log.append(f"{self.player_pokemon.name}'s attack missed!")
            return
        
        # Calculate and apply damage
        damage = self.calculate_damage(self.player_pokemon, self.enemy_pokemon, move)
        self.enemy_pokemon.current_hp -= damage
        
        # Apply status effects
        if move.status_effect and random.random() < move.effect_chance:
            self.enemy_pokemon.apply_status_condition(move.status_effect)
        
        # Apply stat changes
        for stat, stages in move.stat_changes.items():
            self.modify_stat(self.enemy_pokemon, stat, stages)

    def calculate_damage(self, attacker: Pokemon, defender: Pokemon, move: Move) -> int:
        # Calculate damage using Pokemon game formula

        # Skip damage calculation for status moves
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
        
        return max(1, final_damage)  # Minimum 1 damage

    def handle_enemy_turn(self):
        """Handle enemy's turn in battle"""
        # Simple AI: randomly select a move
        available_moves = [m for m in self.enemy_pokemon.moves if m.current_pp > 0]
        if not available_moves:
            self.battle_log.append(f"{self.enemy_pokemon.name} has no moves left!")
            return
        
        move = random.choice(available_moves)
        move.current_pp -= 1
        
        # Check if move hits
        if not self.check_move_hits(self.enemy_pokemon, self.player_pokemon, move):
            self.battle_log.append(f"{self.enemy_pokemon.name}'s attack missed!")
            return
        
        damage = self.calculate_damage(self.enemy_pokemon, self.player_pokemon, move)
        self.player_pokemon.current_hp = max(0, self.player_pokemon.current_hp - damage)
        
        # Effectiveness message
        effectiveness = self.calculate_type_effectiveness(move.type, self.player_pokemon.types)
        if effectiveness > 1:
            self.battle_log.append("It's super effective!")
        elif effectiveness < 1 and effectiveness > 0:
            self.battle_log.append("It's not very effective...")
        elif effectiveness == 0:
            self.battle_log.append("It has no effect...")
        
        # Battle log
        self.battle_log.append(f"{self.enemy_pokemon.name} used {move.name}!")
        
        # Check if fainted
        if self.player_pokemon.current_hp == 0:
            self.battle_state = 'end'
            return
        
        # Switch back to player turn
        self.battle_state = 'player_turn'

    def calculate_type_effectiveness(self, attack_type: str, defender_types: list) -> float:
        """Calculate type effectiveness multiplier"""
        # Type effectiveness chart. We use a simplified version using six instead of 18 types
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
        """Handle player defeat"""
        # Remove defeated Pokemon from Pokedex
        defeated_pokemon = self.player_pokemon.to_dict()
        player_data["pokemons"].remove(defeated_pokemon)
        self.file_handler.save_pokedex(player_data["name"], player_data)
        
        self.show_message(f"{self.player_pokemon.name.capitalize()} has been removed from your Pokedex!")
        self.show_message("You lost! Better luck next time!")

    def draw_battle(self):
        """Draw the battle scene"""
        # Fill background
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
        
        # Draw attack animations if active
        if self.animation_state:
            self.draw_attack_animation()
        
        # Draw HP bars
        self.draw_health_bar(self.enemy_pokemon, (450, 100), False)
        self.draw_health_bar(self.player_pokemon, (50, 300), True)
        
        # Draw battle log with fade effect
        self.draw_battle_log_with_fade()

    def draw_health_bar(self, pokemon: Pokemon, position: tuple, is_player: bool):
        """Draw health bar for Pokemon"""
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
        self.animation_frame += 0.05
        
        # Offset to slow down the animation
        player_y_offset = math.sin(self.animation_frame * 0.5) * 3
        player_pos = (200, 350 + player_y_offset)
        
        # Flip player Pokemon to make him face the enemy
        flipped_sprite = pygame.transform.flip(self.player_pokemon.sprite, True, False)
        self.screen.blit(flipped_sprite, player_pos)
        
        # Enemy Pokemon animation
        enemy_y_offset = math.sin((self.animation_frame * 0.5) + math.pi) * 3
        enemy_pos = (600, 200 + enemy_y_offset)
        self.screen.blit(self.enemy_pokemon.sprite, enemy_pos)

    def add_attack_particles(self, attacker_pos: tuple, target_pos: tuple):
        pass

    def update_and_draw_particles(self):
        pass

    def draw_battle_log_with_fade(self):
        log_surface = pygame.Surface((600, 100))
        log_surface.set_alpha(200)
        log_surface.fill((40, 40, 40))
        
        y = 10
        for i, message in enumerate(self.battle_log[-3:]):
            alpha = 255 - (i * 50)  # Fade old messages
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

    def load_attack_sprites(self):
        sprites = {}
        attack_types = ['normal', 'fire', 'water', 'electric', 'grass']
        
        for attack_type in attack_types:
            try:
                path = os.path.join('images', 'attacks', f'{attack_type}.png')
                sprite = pygame.image.load(path)
                sprites[attack_type] = pygame.transform.scale(sprite, (64, 64))
            except Exception as e:
                print(f"Error loading {attack_type} attack sprite: {e}")
                # Create fallback colored circle
                fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
                pygame.draw.circle(fallback, self.get_type_color(attack_type), 
                                 (32, 32), 32)
                sprites[attack_type] = fallback
        
        return sprites

    def update_battle_animations(self):
        if not self.animation_state:
            return
            
        self.animation_timer += 1
        
        if self.animation_state['type'] == 'attack':
            self.update_attack_animation()
        elif self.animation_state['type'] == 'status':
            self.update_status_animation()

    def update_attack_animation(self):
        anim = self.animation_state
        move = anim['move']
        
        if anim['source'] == 'player':
            start_pos = (200, 350)
            end_pos = (600, 200)
        else:
            start_pos = (600, 200)
            end_pos = (200, 350)
        
        if len(anim['particles']) < self.MOVE_EFFECTS[move['category']]['particles']:
            particle = {
                'pos': list(start_pos),
                'vel': [random.uniform(-1, 1), random.uniform(-1, 1)],
                'life': 1.0
            }
            anim['particles'].append(particle)
        
        for particle in anim['particles']:
            dx = end_pos[0] - particle['pos'][0]
            dy = end_pos[1] - particle['pos'][1]
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 0:
                speed = self.MOVE_EFFECTS[move['category']]['speed']
                particle['pos'][0] += dx/dist * speed
                particle['pos'][1] += dy/dist * speed
            
            particle['life'] -= 0.02
        
        
        anim['particles'] = [p for p in anim['particles'] if p['life'] > 0]
        
        if not anim['particles']:
            self.animation_state = None

    def draw_attack_animation(self):
        if not self.animation_state:
            return
            
        move = self.animation_state['move']
        effect = self.MOVE_EFFECTS[move['category']]
        
        for particle in self.animation_state['particles']:
            alpha = int(255 * particle['life'])
            color = (*effect['color'], alpha)
            
            pygame.draw.circle(
                self.screen,
                color,
                [int(particle['pos'][0]), int(particle['pos'][1])],
                effect['size']
            )

    def draw_status_effects(self):
        """Draw status effect indicators"""
        # Draw status effect indicators for both Pokemon
        pass

    def generate_attack_sprite(self, attack_type: str) -> pygame.Surface:
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        
        if attack_type == 'fire':
            for i in range(8):
                angle = i * (360 / 8)
                points = [
                    (32, 32),
                    (32 + math.cos(math.radians(angle)) * 24,
                     32 + math.sin(math.radians(angle)) * 24),
                    (32 + math.cos(math.radians(angle + 45)) * 16,
                     32 + math.sin(math.radians(angle + 45)) * 16)
                ]
                pygame.draw.polygon(surface, (240, 128, 48, 200), points)
        
        elif attack_type == 'water':
            # Generate water droplets
            for i in range(6):
                x = 16 + (i % 3) * 16
                y = 16 + (i // 3) * 32
                pygame.draw.circle(surface, (104, 144, 240, 200), (x, y), 8)
        
        
        return surface

    def initialize_attack_system(self):
        """Initialize the attack system and create necessary directories"""
        # Create attack sprites directory if it doesn't exist
        os.makedirs('images/attacks', exist_ok=True)
        
        # Generate basic attack sprites if they don't exist
        self.generate_basic_attack_sprites()
        
        # Load attack sprites
        self.attack_sprites = self.load_attack_sprites()

    def generate_basic_attack_sprites(self):
    
        type_colors = {
            'normal': (168, 168, 120),
            'fire': (240, 128, 48),
            'water': (104, 144, 240),
            'electric': (248, 208, 48),
            'grass': (120, 200, 80)
        }
        
        for attack_type, color in type_colors.items():
            sprite = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(sprite, (*color, 200), (32, 32), 24)
            
            # Save sprite to file
            path = os.path.join('images', 'attacks', f'{attack_type}.png')
            pygame.image.save(sprite, path)

    def check_move_hits(self, attacker: Pokemon, defender: Pokemon, move: Move) -> bool:
        """Check if move hits based on accuracy and evasion"""
        if move.accuracy == 0:  
            return True
        
        # Calculate accuracy
        accuracy = move.accuracy
        
        # Random check
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
        
        # Message
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