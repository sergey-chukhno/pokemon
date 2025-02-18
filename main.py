import pygame
import sys
import random
import math
import os
from config import *
from data.api_handler import PokeAPIHandler
from data.data_loader import DataLoader
from models.menu import Menu
from models.battle import BattleSystem
from models.evolution import Evolution

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.api_handler = PokeAPIHandler()
        self.data_loader = DataLoader()
        self.menu = Menu(self.data_loader, self)
        self.clock = pygame.time.Clock()
        self.player_name = None
        self.player_pokemon = []
        self.current_pokemon = None
        
    def initialize_game_data(self):
        if not self.data_loader.pokemons_data:
            self.api_handler.initialize_pokemon_database(INITIAL_POKEMON_COUNT)
            self.data_loader = DataLoader()  
            
    def handle_battle_result(self, result, enemy_pokemon):
        if result == 'victory':
            # Give experience to winning Pokemon
            exp_gain = enemy_pokemon.level * 50
            leveled_up = self.current_pokemon.gain_experience(exp_gain)
            # Show result screen with victory message
            self.show_result_screen("Victory!", 
                f"{enemy_pokemon.name} has been added to your Pokedex!\n"
                f"{self.current_pokemon.name} gained {exp_gain} experience!",
                pokemon=enemy_pokemon,
                is_victory=True)
            
            # Add enemy Pokemon to player's Pokedex with full HP
            enemy_pokemon.current_hp = enemy_pokemon.stats['hp']
            self.player_pokemon.append(enemy_pokemon)
            
            # Check evolution for all Pokemon
            for pokemon in self.player_pokemon:
                evolved_form = self.check_evolution(pokemon)
                if evolved_form:
                    self.handle_evolution(pokemon, evolved_form)
            
            self.data_loader.save_player_pokedex(self.player_name, self.player_pokemon)
            
            # Show Pokedex selection for next battle
            selected_pokemon = self.menu.select_battle_pokemon(self.player_pokemon)
            if selected_pokemon:
                self.current_pokemon = selected_pokemon
                return self.start_battle()
            return False
                
        elif result == 'defeat':
            # Mark the current Pokemon as fainted
            self.current_pokemon.current_hp = 0
            self.data_loader.save_player_pokedex(self.player_name, self.player_pokemon)
            
            # Show result screen with defeat message
            self.show_result_screen("Defeat!", 
                f"{self.current_pokemon.name} has fainted!",
                pokemon=self.current_pokemon,
                is_victory=False)
            
            # Check if any Pokemon are still able to battle
            available_pokemon = [p for p in self.player_pokemon if not p.is_fainted()]
            if not available_pokemon:
                # If no Pokemon can battle, show game over
                self.show_game_over_screen()
                self.player_pokemon = []  
                self.data_loader.save_player_pokedex(self.player_name, self.player_pokemon)
                return False
            
            # Show Pokedex selection for next battle with remaining Pokemons
            selected_pokemon = self.menu.select_battle_pokemon(self.player_pokemon)
            if selected_pokemon and not selected_pokemon.is_fainted():
                self.current_pokemon = selected_pokemon
                return self.start_battle()
            return False
                
        elif result == 'run':
            selected_pokemon = self.menu.select_battle_pokemon(self.player_pokemon)
            if selected_pokemon:
                self.current_pokemon = selected_pokemon
                self.data_loader.save_player_pokedex(self.player_name, self.player_pokemon)
                return self.start_battle()  
            return False
                
        return True
        
    def show_result_screen(self, title, message, pokemon=None, is_victory=True):
        running = True
        animation_time = 0
        float_amplitude = 10
        
        try:
            title_font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 64)
            message_font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 32)
        except:
            title_font = pygame.font.Font(None, 64)
            message_font = pygame.font.Font(None, 32)
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False
            
        
            self.screen.fill(BLACK)
            
            animation_time += 0.1
            float_offset = float_amplitude * math.sin(animation_time)
            
            shadow_offset = 3
            title_shadow = title_font.render(title, True, BLACK)
            title_text = title_font.render(title, True, BRIGHT_YELLOW)
            
            title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//4))
            shadow_rect = title_shadow.get_rect(center=(WINDOW_WIDTH//2 + shadow_offset, 
                                                      WINDOW_HEIGHT//4 + shadow_offset))
            
            self.screen.blit(title_shadow, shadow_rect)
            self.screen.blit(title_text, title_rect)
            
            if pokemon:
                # Scale Pokemon sprite to be larger
                scaled_sprite = pygame.transform.scale(pokemon.sprite, 
                    (pokemon.sprite.get_width() * 3, pokemon.sprite.get_height() * 3))
                
                sprite_rect = scaled_sprite.get_rect(center=(WINDOW_WIDTH//2, 
                                                           WINDOW_HEIGHT//2 + float_offset))
                
                if not is_victory and pokemon.is_fainted():
                    tinted_sprite = scaled_sprite.copy()
                    tinted_sprite.fill((255, 0, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
                    self.screen.blit(tinted_sprite, sprite_rect)
                else:
                    self.screen.blit(scaled_sprite, sprite_rect)
            
            message_shadow = message_font.render(message, True, BLACK)
            message_text = message_font.render(message, True, BRIGHT_YELLOW)
            
            msg_rect = message_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT*3//4))
            shadow_msg_rect = message_shadow.get_rect(center=(WINDOW_WIDTH//2 + shadow_offset, 
                                                            WINDOW_HEIGHT*3//4 + shadow_offset))
            
            self.screen.blit(message_shadow, shadow_msg_rect)
            self.screen.blit(message_text, msg_rect)
            
            prompt_shadow = message_font.render("Press any key to continue...", True, BLACK)
            prompt_text = message_font.render("Press any key to continue...", True, BRIGHT_YELLOW)
            
            prompt_rect = prompt_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 50))
            shadow_prompt_rect = prompt_shadow.get_rect(center=(WINDOW_WIDTH//2 + shadow_offset, 
                                                              WINDOW_HEIGHT - 50 + shadow_offset))
            
            self.screen.blit(prompt_shadow, shadow_prompt_rect)
            self.screen.blit(prompt_text, prompt_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
            
    def show_game_over_screen(self):
        running = True
        animation_time = 0
        float_amplitude = 10
        
        try:
            title_font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 86)
            message_font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 23)  
        except:
            title_font = pygame.font.Font(None, 86)
            message_font = pygame.font.Font(None, 23)  
            
        background = pygame.image.load(os.path.join(MENU_IMAGES_DIR, "menu1.png"))
        background = pygame.transform.scale(background, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        try:
            pikachu_sprite = pygame.image.load(os.path.join(DATA_DIR, 'sprites', '25.png'))  
            pikachu_sprite = pygame.transform.scale(pikachu_sprite, 
                (pikachu_sprite.get_width() * 4, pikachu_sprite.get_height() * 4))  
        except:
            pikachu_sprite = None
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        # Return to menu properly
                        running = False
                        menu_result = self.menu.run()
                        if isinstance(menu_result, tuple):
                            action, player_name = menu_result
                            self.player_name = player_name
                            
                            if action == 'new_game':
                                available_pokemon = [self.data_loader.get_pokemon_by_id(i) 
                                                  for i in range(1, INITIAL_POKEMON_COUNT + 1)]
                                selected_pokemon = self.menu.pokemon_selection_menu(available_pokemon)
                                if selected_pokemon:
                                    self.player_pokemon = selected_pokemon
                                    self.current_pokemon = selected_pokemon[0]
                                    self.data_loader.save_player_pokedex(player_name, selected_pokemon)
                                    self.start_battle()
                                    
                            elif action == 'continue':
                                self.player_pokemon = self.data_loader.load_player_pokedex(player_name)
                                if self.player_pokemon:
                                    self.current_pokemon = self.player_pokemon[0]
                                    self.start_battle()
                        
                        pygame.quit()
                        sys.exit()
                    else:
                        pygame.quit() 
                        sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pygame.quit()
                    sys.exit()
            
            self.screen.blit(background, (0, 0))
            
            animation_time += 0.1
            float_offset = float_amplitude * math.sin(animation_time)
            
            shadow_offset = 3
            title_shadow = title_font.render("GAME OVER", True, BLACK)
            title_text = title_font.render("GAME OVER", True, RED)
            
            title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//4 + 25)) 
            shadow_rect = title_shadow.get_rect(center=(WINDOW_WIDTH//2 + shadow_offset, 
                                                      WINDOW_HEIGHT//4 + 25 + shadow_offset))  
            
            self.screen.blit(title_shadow, shadow_rect)
            self.screen.blit(title_text, title_rect)
            
        
            if pikachu_sprite:
                sprite_rect = pikachu_sprite.get_rect(center=(WINDOW_WIDTH//2, 
                                                             WINDOW_HEIGHT//2 + float_offset))
                self.screen.blit(pikachu_sprite, sprite_rect)  
            
            # Draw continue prompt with shadow
            prompt = "Press any key to quit, press Enter to return to Main Menu..."
            prompt_shadow = message_font.render(prompt, True, BLACK)
            prompt_text = message_font.render(prompt, True, BRIGHT_YELLOW)
            
            prompt_rect = prompt_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 50))
            shadow_prompt_rect = prompt_shadow.get_rect(center=(WINDOW_WIDTH//2 + shadow_offset, 
                                                              WINDOW_HEIGHT - 50 + shadow_offset))
            
            self.screen.blit(prompt_shadow, shadow_prompt_rect)
            self.screen.blit(prompt_text, prompt_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
            
    def check_evolution(self, pokemon):
        if pokemon.level >= pokemon.evolution_level and pokemon.evolution_level > 0:
            print(f"Checking evolution for {pokemon.name} (Level {pokemon.level}, Evolution Level {pokemon.evolution_level})")
            species_data = self.api_handler.fetch_pokemon_species(pokemon.id)
            if species_data and species_data.get('evolves_to'):
                evolved_id = species_data['evolves_to'][0]['species']['url'].split('/')[-2]
                print(f"{pokemon.name} can evolve into Pokemon #{evolved_id}!")
                return self.data_loader.get_pokemon_by_id(int(evolved_id))
        return None
        
    def handle_evolution(self, pokemon, evolved_form):
    
        evolution = Evolution(self.screen, pokemon, evolved_form)
        evolved_pokemon = evolution.run()
        
        if evolved_pokemon:
            # Replace old Pokemon with evolved form
            for i, p in enumerate(self.player_pokemon):
                if p.id == pokemon.id:
                    self.player_pokemon[i] = evolved_pokemon
                    break
            self.data_loader.save_player_pokedex(self.player_name, self.player_pokemon)
            
    def start_battle(self):
        # Ensure current Pokemon has HP before battle
        if self.current_pokemon.current_hp <= 0:
            self.current_pokemon.current_hp = self.current_pokemon.stats['hp']
            
        # Select random enemy Pokemon from those not in player's Pokedex
        available_pokemon = [self.data_loader.get_pokemon_by_id(i) 
                           for i in range(1, INITIAL_POKEMON_COUNT + 1)
                           if self.data_loader.get_pokemon_by_id(i) not in self.player_pokemon]
        
        if not available_pokemon:
            self.show_result_screen("Congratulations!", "You've caught all available Pokemon!")
            return False
            
        enemy_pokemon = random.choice(available_pokemon)
        enemy_pokemon.current_hp = enemy_pokemon.stats['hp']
        
        # Initialize battle 
        battle = BattleSystem(self.screen, self.current_pokemon, enemy_pokemon)
        battle.all_player_pokemon = self.player_pokemon
        result = battle.run()
        
        if result == 'quit':
            return False
            
        return self.handle_battle_result(result, enemy_pokemon)
        
    def run(self):
        self.initialize_game_data()
        
        while True:
            menu_result = self.menu.run()
            
            if menu_result == 'quit':
                break
            elif isinstance(menu_result, tuple):
                action, player_name = menu_result
                self.player_name = player_name
                
                if action == 'new_game':
                    available_pokemon = [self.data_loader.get_pokemon_by_id(i) 
                                      for i in range(1, INITIAL_POKEMON_COUNT + 1)]
                    selected_pokemon = self.menu.pokemon_selection_menu(available_pokemon)
                    if selected_pokemon:
                        self.player_pokemon = selected_pokemon
                        self.current_pokemon = selected_pokemon[0]
                        self.data_loader.save_player_pokedex(player_name, selected_pokemon)
                        if not self.start_battle():
                            break
                            
                elif action == 'continue':
                    self.player_pokemon = self.data_loader.load_player_pokedex(player_name)
                    if self.player_pokemon:
                        self.current_pokemon = self.player_pokemon[0]  # Set initial Pokemon
                        if not self.start_battle():
                            break
                            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run() 