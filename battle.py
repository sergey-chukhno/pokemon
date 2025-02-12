import pygame
import random
import os
import math
from typing import Dict, Optional
from models.pokemon import Pokemon
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
        self.turn_state = "player_turn"  # or "enemy_turn"
        
        # Load battle background
        self.background = pygame.Surface(screen.get_size())
        self.background.fill(self.WHITE)
        
        # Add new attributes for battle scene
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

    def start(self, player_data: Dict) -> Dict:
        # Initialize battle
        self.player_pokemon = Pokemon.from_dict(player_data["pokemons"][0])
        self.enemy_pokemon = self.select_random_enemy()
        self.battle_log = []
        self.turn_state = "player_turn"
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return {"action": "quit"}
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return {"action": "return_to_menu"}
                    
                    if self.turn_state == "player_turn":
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                            # Handle player attack
                            self.handle_player_turn(event.key - pygame.K_1)
                            
                            # Check for battle end
                            if self.enemy_pokemon.current_hp <= 0:
                                self.handle_victory(player_data)
                                return {"action": "return_to_menu"}
                            
                            # Enemy turn
                            self.turn_state = "enemy_turn"
                    
                    elif self.turn_state == "enemy_turn" and event.key == pygame.K_RETURN:
                        # Handle enemy attack
                        self.handle_enemy_turn()
                        
                        # Check for battle end
                        if self.player_pokemon.current_hp <= 0:
                            self.handle_defeat(player_data)
                            return {"action": "return_to_menu"}
                        
                        # Player turn
                        self.turn_state = "player_turn"

            self.draw_battle()
            pygame.display.flip()

    def select_random_enemy(self) -> Pokemon:
        """Select a random Pokemon as enemy"""
        enemy_data = random.choice(list(self.pokemons.values()))
        return Pokemon.from_dict(enemy_data.to_dict())

    def handle_player_turn(self, move_index: int):
        """Handle player's attack"""
        # Calculate damage (simplified)
        base_damage = self.player_pokemon.stats["attack"] // 2
        
        # Apply type effectiveness
        multiplier = self.calculate_type_effectiveness(
            self.player_pokemon.types[0], 
            self.enemy_pokemon.types
        )
        
        final_damage = int(base_damage * multiplier)
        self.enemy_pokemon.current_hp = max(0, self.enemy_pokemon.current_hp - final_damage)
        
        # Add to battle log
        effectiveness_text = ""
        if multiplier > 1:
            effectiveness_text = "It's super effective!"
        elif multiplier < 1:
            effectiveness_text = "It's not very effective..."
            
        self.battle_log.append(
            f"{self.player_pokemon.name} attacks for {final_damage} damage! {effectiveness_text}"
        )

    def handle_enemy_turn(self):
        """Handle enemy's attack"""
        # Calculate damage (simplified)
        base_damage = self.enemy_pokemon.stats["attack"] // 2
        
        # Apply type effectiveness
        multiplier = self.calculate_type_effectiveness(
            self.enemy_pokemon.types[0], 
            self.player_pokemon.types
        )
        
        final_damage = int(base_damage * multiplier)
        self.player_pokemon.current_hp = max(0, self.player_pokemon.current_hp - final_damage)
        
        # Add to battle log
        effectiveness_text = ""
        if multiplier > 1:
            effectiveness_text = "It's super effective!"
        elif multiplier < 1:
            effectiveness_text = "It's not very effective..."
            
        self.battle_log.append(
            f"{self.enemy_pokemon.name} attacks for {final_damage} damage! {effectiveness_text}"
        )

    def calculate_type_effectiveness(self, attack_type: str, defender_types: list) -> float:
        """Calculate type effectiveness multiplier"""
        # Type effectiveness chart (simplified)
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
        """Handle player victory"""
        # Grant experience
        exp_gain = self.enemy_pokemon.level * 50
        self.player_pokemon.gain_experience(exp_gain)
        
        # Add defeated Pokemon to player's Pokedex
        captured_pokemon = self.enemy_pokemon.to_dict()
        if captured_pokemon not in player_data["pokemons"]:
            player_data["pokemons"].append(captured_pokemon)
            self.show_message(f"Added {self.enemy_pokemon.name.capitalize()} to your Pokedex!")
        
        # Check for evolution
        if self.player_pokemon.can_evolve():
            self.show_evolution_animation()
            self.player_pokemon.evolve()
        
        # Update player's Pokemon in Pokedex
        player_data["pokemons"][0] = self.player_pokemon.to_dict()
        self.file_handler.save_pokedex(player_data["name"], player_data)
        
        # Show victory message
        self.show_message(f"Victory! Gained {exp_gain} experience!")

    def handle_defeat(self, player_data: Dict):
        """Handle player defeat"""
        # Remove defeated Pokemon from Pokedex
        defeated_pokemon = self.player_pokemon.to_dict()
        player_data["pokemons"].remove(defeated_pokemon)
        self.file_handler.save_pokedex(player_data["name"], player_data)
        
        self.show_message(f"{self.player_pokemon.name.capitalize()} has been removed from your Pokedex!")
        self.show_message("Defeat! Better luck next time!")

    def draw_battle(self):
        """Draw enhanced battle scene"""
        # Select and draw background based on Pokemon types
        bg_type = self.select_background_type()
        self.screen.blit(self.battle_backgrounds.get(bg_type, self.background), (0, 0))
        
        # Draw Pokemon with animations
        self.draw_animated_pokemon()
        
        # Draw modern health bars with adjusted positions
        self.draw_modern_health_bar(self.enemy_pokemon, (450, 100), is_player=False)
        self.draw_modern_health_bar(self.player_pokemon, (50, 250), is_player=True)
        
        # Draw particle effects
        self.update_and_draw_particles()
        
        # Draw battle log with fade effect
        self.draw_battle_log_with_fade()

    def draw_modern_health_bar(self, pokemon: Pokemon, position: tuple, is_player: bool):
        """Draw a modern-looking health bar"""
        x, y = position
        max_hp = pokemon.stats["hp"]
        current_hp = pokemon.current_hp
        hp_percentage = current_hp / max_hp
        
        # Determine health bar color
        if hp_percentage > 0.5:
            color = self.HP_COLORS['high']
        elif hp_percentage > 0.25:
            color = self.HP_COLORS['medium']
        else:
            color = self.HP_COLORS['low']
        
        # Draw name plate with increased width (+20 pixels total)
        name_plate = pygame.Surface((270, 80))  # Increased from 260 to 270
        name_plate.set_alpha(200)
        name_plate.fill((40, 40, 40))
        self.screen.blit(name_plate, (x - 10, y - 10))
        
        # Use slightly smaller font for Pokemon name and level
        name_font = pygame.font.Font(None, 32)  # Reduced from 36
        self.draw_text(f"{pokemon.name.capitalize()} Lv.{pokemon.level}",
                      (x, y), name_font, self.WHITE)
        
        # Draw HP bar background with increased width (+20 pixels total)
        bar_bg = pygame.Rect(x, y + 30, 220, self.HP_BAR_HEIGHT)  # Increased from 210 to 220
        pygame.draw.rect(self.screen, (40, 40, 40), bar_bg)
        
        # Draw HP bar with smooth animation and increased width
        bar_width = int(220 * hp_percentage)  # Increased from 210 to 220
        bar_rect = pygame.Rect(x, y + 30, bar_width, self.HP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, color, bar_rect)
        
        # Draw border
        pygame.draw.rect(self.screen, self.WHITE, bar_bg, self.HP_BAR_BORDER)
        
        # Draw HP numbers with smaller font
        hp_font = pygame.font.Font(None, 20)  # Reduced from 24
        hp_text = f"{current_hp}/{max_hp}"
        self.draw_text(hp_text, (x + 230, y + 30),  # Increased from 220 to 230
                      hp_font, self.WHITE)

    def draw_animated_pokemon(self):
        """Draw Pokemon with idle animations"""
        # Reduce animation speed (from 0.2 to 0.05)
        self.animation_frame += 0.05
        
        # Reduce amplitude (from 5 to 3) and slow down sine wave
        player_y_offset = math.sin(self.animation_frame * 0.5) * 3
        # Move player Pokemon up 50 pixels (from y=400 to y=350)
        player_pos = (200, 350 + player_y_offset)
        
        # Flip player Pokemon sprite horizontally
        flipped_sprite = pygame.transform.flip(self.player_pokemon.sprite, True, False)
        self.screen.blit(flipped_sprite, player_pos)
        
        # Enemy Pokemon animation (unchanged)
        enemy_y_offset = math.sin((self.animation_frame * 0.5) + math.pi) * 3
        enemy_pos = (600, 200 + enemy_y_offset)
        self.screen.blit(self.enemy_pokemon.sprite, enemy_pos)

    def add_attack_particles(self, attacker_pos: tuple, target_pos: tuple):
        """Add particle effects for attacks"""
        # Add various particle effects based on attack type
        pass

    def update_and_draw_particles(self):
        """Update and draw particle effects"""
        # Update particle positions and draw them
        pass

    def draw_battle_log_with_fade(self):
        """Draw battle log with fade effect"""
        log_surface = pygame.Surface((600, 100))
        log_surface.set_alpha(200)
        log_surface.fill((40, 40, 40))
        
        y = 10
        for i, message in enumerate(self.battle_log[-3:]):
            alpha = 255 - (i * 50)  # Fade out older messages
            text_surface = self.info_font.render(message, True, self.WHITE)
            text_surface.set_alpha(alpha)
            log_surface.blit(text_surface, (10, y))
            y += 30
            
        self.screen.blit(log_surface, (100, 500))

    def draw_text(self, text: str, position: tuple, font: pygame.font.Font, 
                 color: tuple = None, center: bool = False):
        """Helper method to draw text"""
        if color is None:
            color = self.BLACK
        text_surface = font.render(text, True, color)
        if center:
            text_rect = text_surface.get_rect(center=position)
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, position)

    def show_message(self, message: str, duration: int = 2000):
        """Show a message on screen"""
        self.screen.fill(self.WHITE)
        self.draw_text(message, (400, 300), self.battle_font, center=True)
        pygame.display.flip()
        pygame.time.wait(duration)

    def show_evolution_animation(self):
        """Show evolution animation"""
        original_sprite = self.player_pokemon.sprite
        
        # Simple evolution animation
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
        """Load different battle backgrounds for variety"""
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
        """Select appropriate background type based on Pokemon types"""
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

def platform_gradient(surface: pygame.Surface, color1: tuple, color2: tuple):
    """Create a gradient effect on a surface from color1 to color2"""
    height = surface.get_height()
    for y in range(height):
        # Calculate color for this line
        factor = y / height
        current_color = [
            int(color1[i] + (color2[i] - color1[i]) * factor)
            for i in range(3)
        ]
        # Draw horizontal line
        pygame.draw.line(surface, current_color, 
                        (0, y), (surface.get_width(), y))