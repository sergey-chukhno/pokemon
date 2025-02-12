import pygame
import random
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
        """Draw the battle screen"""
        self.screen.fill(self.WHITE)
        
        # Draw Pokemon sprites
        # Player Pokemon (bottom left)
        player_sprite_rect = self.player_pokemon.sprite.get_rect(center=(200, 400))
        self.screen.blit(self.player_pokemon.sprite, player_sprite_rect)
        
        # Enemy Pokemon (top right)
        enemy_sprite_rect = self.enemy_pokemon.sprite.get_rect(center=(600, 200))
        self.screen.blit(self.enemy_pokemon.sprite, enemy_sprite_rect)
        
        # Draw Pokemon info
        self.draw_pokemon_info(self.player_pokemon, (50, 450))
        self.draw_pokemon_info(self.enemy_pokemon, (450, 50))
        
        # Draw battle log
        log_y = 500
        for message in self.battle_log[-3:]:  # Show last 3 messages
            self.draw_text(message, (400, log_y), self.info_font, center=True)
            log_y += 30
        
        # Draw turn indicator
        if self.turn_state == "player_turn":
            self.draw_text("Your turn! (1-4 to attack)", (400, 30), self.battle_font, center=True)
        else:
            self.draw_text("Enemy turn! (Press Enter)", (400, 30), self.battle_font, center=True)

    def draw_pokemon_info(self, pokemon: Pokemon, position: tuple):
        """Draw Pokemon information"""
        x, y = position
        
        # Draw name and level
        self.draw_text(f"{pokemon.name.capitalize()} Lv.{pokemon.level}", 
                      (x, y), self.battle_font)
        
        # Draw HP bar
        hp_percent = pokemon.current_hp / pokemon.stats["hp"]
        bar_width = 200
        bar_height = 20
        pygame.draw.rect(self.screen, self.RED, 
                        (x, y + 30, bar_width, bar_height))
        pygame.draw.rect(self.screen, self.GREEN,
                        (x, y + 30, bar_width * hp_percent, bar_height))
        
        # Draw HP numbers
        self.draw_text(f"HP: {pokemon.current_hp}/{pokemon.stats['hp']}", 
                      (x, y + 60), self.info_font)

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