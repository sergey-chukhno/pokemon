import pygame
import sys
import os
from typing import Dict, List, Optional, Tuple
from data_manager.file_handler import FileHandler
from models.pokemon import Pokemon

class MenuSystem:
    def __init__(self, screen: pygame.Surface, pokemons: Dict):
        self.screen = screen
        self.pokemons = pokemons
        self.file_handler = FileHandler()
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.GRAY = (128, 128, 128)
        self.YELLOW = (255, 255, 0)
        self.BRIGHT_YELLOW = (255, 255, 128) 
        
        
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 80)  
        self.menu_font = pygame.font.Font(None, 52)   
        self.info_font = pygame.font.Font(None, 40)    
        
        # Load background
        self.background = self.load_background()

    def load_background(self) -> pygame.Surface:

        try:
            image_path = os.path.join('images', 'menu1.png')
            
            # Load and scale image to screen size
            image = pygame.image.load(image_path)
            return pygame.transform.scale(image, self.screen.get_size())
        except Exception as e:
            print(f"Error loading background: {e}")
            # Return plain background as fallback
            fallback = pygame.Surface(self.screen.get_size())
            fallback.fill(self.WHITE)
            return fallback

    def show_main_menu(self) -> Dict:
        options = ["New Player", "Existing Player", "Options", "Quit"]
        selected = 0
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return {"action": "quit"}
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(options)
                    elif event.key == pygame.K_RETURN:
                        if options[selected] == "New Player":
                            return self.new_player_flow()
                        elif options[selected] == "Existing Player":
                            return self.load_player_flow()
                        elif options[selected] == "Options":
                            self.show_options()
                        elif options[selected] == "Quit":
                            return {"action": "quit"}

            
            self.screen.blit(self.background, (0, 0))
            
        
            title = "BATTLE OF POKEMONS"
            shadow_offsets = [(3, 3), (-3, -3), (3, -3), (-3, 3)]
            for dx, dy in shadow_offsets:
                self.draw_text(title, (403 + dx, 73 + dy), self.title_font, self.BLACK, center=True)
            self.draw_text(title, (400, 70), self.title_font, self.BRIGHT_YELLOW, center=True)
            
            # Draw menu options
            for i, option in enumerate(options):
                y_pos = 300 + i * 70
                if i == selected:
                    text_surface = self.menu_font.render(option, True, self.BRIGHT_YELLOW)
                    text_rect = text_surface.get_rect(center=(400, y_pos))
                    box_rect = text_rect.inflate(60, 30)
                    pygame.draw.rect(self.screen, self.BLACK, box_rect)
                    pygame.draw.rect(self.screen, self.BRIGHT_YELLOW, box_rect, 4) 
                    self.draw_text(option, (400, y_pos), self.menu_font, self.WHITE, center=True)
                else:
                    for dx, dy in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                        self.draw_text(option, (400 + dx, y_pos + dy), self.menu_font, self.BLACK, center=True)
                    self.draw_text(option, (400, y_pos), self.menu_font, self.BRIGHT_YELLOW, center=True)
            
            hint_text = "Use UP/DOWN to navigate, ENTER to select"
            for dx, dy in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                self.draw_text(hint_text, (450 + dx, 570 + dy), self.info_font, self.BLACK, center=True)
            self.draw_text(hint_text, (450, 570), self.info_font, self.BRIGHT_YELLOW, center=True)
            
            pygame.display.flip()

    def new_player_flow(self) -> Optional[Dict]:
        player_name = self.get_text_input("Enter your name:")
        if not player_name:
            return None
            
        # Show Pokemon selection
        selected_pokemon = self.pokemon_selection_menu()
        if not selected_pokemon:
            return None
            
        # Create player data
        player_data = {
            "name": player_name,
            "pokemons": [selected_pokemon.to_dict()]
        }
        
        # Save to Player's Pokedex
        self.file_handler.save_pokedex(player_name, player_data)
        
        # Return battle action instead of just player data
        return {"action": "battle", "player_data": player_data}

    def load_player_flow(self) -> Optional[Dict]:
        player_name = self.get_text_input("Enter your name:")
        if not player_name:
            return None
            
        player_data = self.file_handler.load_pokedex(player_name)
        if not player_data:
            self.show_message("No save data found!")
            return None

        # Check if Pokedex is empty
        if not player_data["pokemons"]:
            self.show_message("Your Pokedex is empty! Select a new Pokemon.")
            selected_pokemon = self.pokemon_selection_menu()
            if not selected_pokemon:
                return None
            player_data["pokemons"] = [selected_pokemon.to_dict()]
            self.file_handler.save_pokedex(player_name, player_data)
        else:
            # Let player select from their Pokedex
            selected_pokemon = self.pokedex_selection_menu(player_data["pokemons"])
            if not selected_pokemon:
                return None
            # Put the selected Pokemon first in the list
            player_data["pokemons"].remove(selected_pokemon.to_dict())
            player_data["pokemons"].insert(0, selected_pokemon.to_dict())
            self.file_handler.save_pokedex(player_name, player_data)
            
        return {"action": "battle", "player_data": player_data}

    def pokemon_selection_menu(self):
        # Load pokeball background with direct path
        try:
            image_path = os.path.join('images', 'pokeball.png')
            bg_image = pygame.image.load(image_path)
            bg_image = pygame.transform.scale(bg_image, self.screen.get_size())
        except Exception as e:
            print(f"Error loading pokeball background: {e}")
            bg_image = None 

        pokemon_list = list(self.pokemons.values())
        selected = 0
        scroll_offset = 0
        pokemons_per_page = 3
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = max(0, selected - 1)
                    elif event.key == pygame.K_DOWN:
                        selected = min(len(pokemon_list) - 1, selected + 1)
                    elif event.key == pygame.K_RETURN:
                        return pokemon_list[selected]
                    elif event.key == pygame.K_ESCAPE:
                        return None

            if selected >= scroll_offset + pokemons_per_page:
                scroll_offset += 1
            elif selected < scroll_offset:
                scroll_offset -= 1

            if bg_image:
                self.screen.blit(bg_image, (0, 0))
            else:
                self.screen.fill(self.BLACK)
            
            title = "SELECT YOUR POKEMON"
            for dx, dy in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                self.draw_text(title, (400 + dx, 70 + dy), self.title_font, self.BLACK, center=True)
            self.draw_text(title, (400, 70), self.title_font, self.BRIGHT_YELLOW, center=True)
            
            for i in range(pokemons_per_page):
                idx = scroll_offset + i
                if idx >= len(pokemon_list):
                    break
                    
                pokemon = pokemon_list[idx]
                color = self.BRIGHT_YELLOW if idx == selected else self.WHITE
                y_pos = 180 + i * 150 
                
                if idx == selected:
                    info_rect = pygame.Rect(230, y_pos - 20, 460, 140) 
                    pygame.draw.rect(self.screen, self.BLACK, info_rect)
                    pygame.draw.rect(self.screen, self.BRIGHT_YELLOW, info_rect, 4)
                
                scaled_sprite = pygame.transform.scale(pokemon.sprite, (192, 192))
                sprite_rect = scaled_sprite.get_rect(center=(150, y_pos + 50))
                self.screen.blit(scaled_sprite, sprite_rect)
                
                name_text = f"{pokemon.name.capitalize()}"
                stats_text = f"HP: {pokemon.stats['hp']} ATK: {pokemon.stats['attack']}"
                types_text = f"Types: {', '.join(pokemon.types)}"
                
                for text, y_offset in [(name_text, 0), (stats_text, 30), (types_text, 60)]:
                    for dx, dy in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                        self.draw_text(text, (280 + dx, y_pos + y_offset + dy), 
                                     self.menu_font, self.BLACK)
                    self.draw_text(text, (280, y_pos + y_offset), self.menu_font, color)
            
            pygame.display.flip()

    def pokedex_selection_menu(self, pokemon_list: List[Dict]) -> Optional[Pokemon]:
        menu3_path = os.path.join('images', 'menu3.png')

        
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            absolute_path = os.path.join(current_dir, '..', 'images', 'menu3.png')
            bg_image = pygame.image.load(absolute_path)
            bg_image = pygame.transform.scale(bg_image, self.screen.get_size())
        except Exception as e:
            print(f"Error loading menu3 background: {e}")
            bg_image = self.background 

        pokemons = [Pokemon.from_dict(p) for p in pokemon_list]
        selected = 0
        scroll_offset = 0
        pokemons_per_page = 3
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = max(0, selected - 1)
                    elif event.key == pygame.K_DOWN:
                        selected = min(len(pokemons) - 1, selected + 1)
                    elif event.key == pygame.K_RETURN:
                        return pokemons[selected]
                    elif event.key == pygame.K_ESCAPE:
                        return None

            if selected >= scroll_offset + pokemons_per_page:
                scroll_offset += 1
            elif selected < scroll_offset:
                scroll_offset -= 1

            self.screen.blit(bg_image, (0, 0))
            
            title = "SELECT FROM YOUR POKEDEX"
            for dx, dy in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                self.draw_text(title, (400 + dx, 70 + dy), self.title_font, self.BLACK, center=True)
            self.draw_text(title, (400, 70), self.title_font, self.BRIGHT_YELLOW, center=True)
            
            for i in range(pokemons_per_page):
                idx = scroll_offset + i
                if idx >= len(pokemons):
                    break
                    
                pokemon = pokemons[idx]
                color = self.BRIGHT_YELLOW if idx == selected else self.WHITE
                y_pos = 180 + i * 150
                
                if idx == selected:
                    info_rect = pygame.Rect(230, y_pos - 20, 400, 140)
                    pygame.draw.rect(self.screen, self.BLACK, info_rect)
                    pygame.draw.rect(self.screen, self.BRIGHT_YELLOW, info_rect, 4)
                
                scaled_sprite = pygame.transform.scale(pokemon.sprite, (192, 192))
                sprite_rect = scaled_sprite.get_rect(center=(150, y_pos + 50))
                self.screen.blit(scaled_sprite, sprite_rect)
                

                name_text = f"{pokemon.name.capitalize()} (Lv.{pokemon.level})"
                stats_text = f"HP: {pokemon.stats['hp']} ATK: {pokemon.stats['attack']}"
                types_text = f"Types: {', '.join(pokemon.types)}"
                
                for text, y_offset in [(name_text, 0), (stats_text, 30), (types_text, 60)]:
                    for dx, dy in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                        self.draw_text(text, (280 + dx, y_pos + y_offset + dy), 
                                     self.menu_font, self.BLACK)
                    self.draw_text(text, (280, y_pos + y_offset), self.menu_font, color)

            # Draw navigation hint message
            hint_text = "Use UP/DOWN to navigate, ENTER to select, ESC to cancel"
            for dx, dy in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                self.draw_text(hint_text, (450 + dx, 570 + dy), self.info_font, self.BLACK, center=True)
            self.draw_text(hint_text, (450, 570), self.info_font, self.BRIGHT_YELLOW, center=True)
            
            pygame.display.flip()

    def get_text_input(self, prompt: str) -> Optional[str]:
        try:
            bg_image = pygame.image.load(os.path.join('images', 'menu2.png'))
            bg_image = pygame.transform.scale(bg_image, self.screen.get_size())
        except Exception as e:
            print(f"Error loading menu2 background: {e}")
            bg_image = self.background 

        text = ""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and text:
                        return text
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.unicode.isprintable():
                        text += event.unicode

            self.screen.blit(bg_image, (0, 0))
            
            for dx, dy in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                self.draw_text(prompt, (400 + dx, 200 + dy), self.menu_font, self.BLACK, center=True)
            
            self.draw_text(prompt, (400, 200), self.menu_font, self.BRIGHT_YELLOW, center=True)
            

            if text:
                text_surface = self.menu_font.render(text, True, self.BRIGHT_YELLOW)
                text_rect = text_surface.get_rect(center=(400, 300))
                
                box_rect = text_rect.inflate(60, 30)
                pygame.draw.rect(self.screen, self.BLACK, box_rect)
                pygame.draw.rect(self.screen, self.BRIGHT_YELLOW, box_rect, 4)
                
                for dx, dy in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                    self.draw_text(text, (400 + dx, 300 + dy), self.menu_font, self.BLACK, center=True)
                self.draw_text(text, (400, 300), self.menu_font, self.BRIGHT_YELLOW, center=True)
            else:
                if pygame.time.get_ticks() % 1000 < 500:  # Blink every half second
                    cursor_rect = pygame.Rect(395, 290, 10, 30)
                    pygame.draw.rect(self.screen, self.BRIGHT_YELLOW, cursor_rect)
            
            instruction = "Press ENTER to confirm, ESC to cancel"
            for dx, dy in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                self.draw_text(instruction, (450 + dx, 570 + dy), self.info_font, self.BLACK, center=True)
            self.draw_text(instruction, (450, 570), self.info_font, self.BRIGHT_YELLOW, center=True)
            
            pygame.display.flip()

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
        self.draw_text(message, (400, 300), self.menu_font, center=True)
        pygame.display.flip()
        pygame.time.wait(duration) 