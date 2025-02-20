import pygame
import os
from config import *
from data.data_loader import load_player_pokedex

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
        try:
            self.font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 32)  
        except:
            self.font = pygame.font.Font(None, 32)

        # Load sounds with error handling
        try:
            self.hover_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "hover.mp3"))
            self.select_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "click.mp3"))
        except:
            print("Warning: Could not load button sound effects")
            self.hover_sound = None
            self.select_sound = None
            
        self.hover_sound_played = False
        
    def draw(self, screen):
        if hasattr(self, 'custom_draw'):
            self.custom_draw(screen)
        else:
            button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, BUTTON_BLACK, button_surface.get_rect(), border_radius=15)
            screen.blit(button_surface, self.rect)
            
            border_color = BRIGHT_YELLOW if self.is_hovered else BLACK
            border_width = 3 if self.is_hovered else 2
            pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=15)
            
            text_surface = self.font.render(self.text, True, BRIGHT_YELLOW)
            text_rect = text_surface.get_rect()
            text_rect.centerx = self.rect.centerx
            text_rect.centery = self.rect.centery + 11
            screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            if self.is_hovered and not was_hovered and self.hover_sound:
                self.hover_sound.play()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                if self.select_sound:
                    self.select_sound.play()
                return True
        return False

class Menu:
    def __init__(self, game, pokemons_data):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Pokemon Battle Game")
        self.clock = pygame.time.Clock()
        self.game = game
        self.pokemons_data = pokemons_data
        
        # Load font with fallback
        try:
            self.font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 32)
        except:
            print("Warning: Could not load Pokemon font, using default")
            self.font = pygame.font.Font(None, 32)
            
        self.setup_buttons()
        
        # Load background with fallback
        try:
            self.background = pygame.image.load(os.path.join(MENU_IMAGES_DIR, "menu1.png"))
            self.background = pygame.transform.scale(self.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
        except:
            print("Warning: Could not load menu background, using solid color")
            self.background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.background.fill((50, 50, 50))  # Dark gray background as fallback
        
    def setup_buttons(self):
        button_width = 220  
        button_height = 60  
        center_x = WINDOW_WIDTH // 2 - button_width // 2
        
        self.buttons = {
            'new_game': Button(center_x, 300, button_width, button_height, 
                             "New Game", BUTTON_BLACK, BUTTON_BLACK),
            'continue': Button(center_x, 380, button_width, button_height,
                             "Continue", BUTTON_BLACK, BUTTON_BLACK),
            'quit': Button(center_x, 460, button_width, button_height,
                          "Quit", BUTTON_BLACK, BUTTON_BLACK)
        }
        
    def draw(self):
        self.screen.blit(self.background, (0, 0))
        
        for button in self.buttons.values():
            button.draw(self.screen)
            
        pygame.display.flip()
        
    def get_player_name(self):
        input_text = ""
        try:
            prompt_font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 48)  
            input_font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 32)  
        except:
            prompt_font = pygame.font.Font(None, 48)
            input_font = pygame.font.Font(None, 32)
            
        typing_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "typing.mp3"))
        select_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "click.mp3"))
        
        background = pygame.image.load(os.path.join(MENU_IMAGES_DIR, "menu2.png"))
        background = pygame.transform.scale(background, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and input_text.strip():
                        select_sound.play()
                        return input_text.strip()
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                        typing_sound.play()
                    else:
                        input_text += event.unicode
                        typing_sound.play()
                        
            self.screen.blit(background, (0, 0))
            
            prompt = "Enter your name:"
            shadow = prompt_font.render(prompt, True, BLACK)
            text = prompt_font.render(prompt, True, BRIGHT_YELLOW)
            
            prompt_y = WINDOW_HEIGHT//2 - 80  
            self.screen.blit(shadow, (WINDOW_WIDTH//2 - shadow.get_width()//2 + 2, prompt_y + 2))
            self.screen.blit(text, (WINDOW_WIDTH//2 - text.get_width()//2, prompt_y))
            
            box_width = 400
            box_height = 70
            box_x = WINDOW_WIDTH//2 - box_width//2
            box_y = WINDOW_HEIGHT//2 + 10
            
            input_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            pygame.draw.rect(input_surface, BUTTON_BLACK, input_surface.get_rect(), border_radius=15)
            self.screen.blit(input_surface, (box_x, box_y))
            
            pygame.draw.rect(self.screen, BRIGHT_YELLOW, 
                           (box_x, box_y, box_width, box_height), 2, border_radius=15)
            
            if input_text:
                input_render = input_font.render(input_text, True, BRIGHT_YELLOW)
                text_x = box_x + (box_width - input_render.get_width())//2
                text_y = box_y + (box_height - input_render.get_height())//2 + 11
                self.screen.blit(input_render, (text_x, text_y))
            
            if len(input_text) < 12 and pygame.time.get_ticks() % 1000 < 500:
                cursor_x = box_x + (box_width - input_font.size(input_text)[0])//2 + input_font.size(input_text)[0]
                pygame.draw.line(self.screen, BRIGHT_YELLOW,
                               (cursor_x, box_y + 20),
                               (cursor_x, box_y + box_height - 20), 2)
            
            pygame.display.flip()
            self.clock.tick(FPS)
            
    def pokemon_selection_menu(self, available_pokemon, is_pokedex=False, is_battle_select=False):
        selected_pokemon = []
        current_selection = 0
        
        
        available_pokemon = list(dict.fromkeys(available_pokemon))  
        
        if is_battle_select:
            for i, pokemon in enumerate(available_pokemon):
                if not pokemon.is_fainted():
                    current_selection = i
                    break
        
    
        background = pygame.image.load(os.path.join(MENU_IMAGES_DIR, "pokeball.png"))
        background = pygame.transform.scale(background, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        try:
            title_font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 48)
            info_font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 24)
        except:
            title_font = pygame.font.Font(None, 48)
            info_font = pygame.font.Font(None, 24)
            
        pokemon_height = 120
        start_y = 180
        visible_pokemon = 3
        scroll_offset = 0
        box_width = int(WINDOW_WIDTH * 0.8)
        box_x_offset = 30
        
        select_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "click.mp3"))
        hover_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "hover.mp3"))
        
        title = "Select Battle Pokemon" if is_battle_select else ("Your Pokedex" if is_pokedex else "Select Your Pokemon")
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_UP:
                        # Circular scrolling 
                        if current_selection > 0:
                            next_selection = current_selection - 1
                        else:
                            next_selection = len(available_pokemon) - 1
                            
                        if is_battle_select:
                            while next_selection != current_selection and available_pokemon[next_selection].is_fainted():
                                next_selection = (next_selection - 1) if next_selection > 0 else len(available_pokemon) - 1
                            if not available_pokemon[next_selection].is_fainted():
                                current_selection = next_selection
                        else:
                            current_selection = next_selection
                            
                        # Adjust scroll offset for circular scrolling
                        if current_selection >= len(available_pokemon) - visible_pokemon:
                            scroll_offset = len(available_pokemon) - visible_pokemon
                        elif current_selection < scroll_offset:
                            scroll_offset = current_selection
                        hover_sound.play()
                            
                    elif event.key == pygame.K_DOWN:
                        # Circular scrolling down
                        if current_selection < len(available_pokemon) - 1:
                            next_selection = current_selection + 1
                        else:
                            next_selection = 0
                            
                        if is_battle_select:
                            while next_selection != current_selection and available_pokemon[next_selection].is_fainted():
                                next_selection = (next_selection + 1) % len(available_pokemon)
                            if not available_pokemon[next_selection].is_fainted():
                                current_selection = next_selection
                        else:
                            current_selection = next_selection
                            
                        if current_selection >= scroll_offset + visible_pokemon:
                            scroll_offset = current_selection - visible_pokemon + 1
                        elif current_selection < visible_pokemon:
                            scroll_offset = 0
                        hover_sound.play()
                    elif event.key == pygame.K_RETURN:
                        if is_battle_select:
                            pokemon = available_pokemon[current_selection]
                            if not pokemon.is_fainted():
                                select_sound.play()
                                return pokemon
                        elif not is_pokedex:
                            pokemon = available_pokemon[current_selection]
                            if pokemon not in selected_pokemon:
                                selected_pokemon.append(pokemon)
                                select_sound.play()
                                if len(selected_pokemon) >= MAX_PLAYER_POKEMON:
                                    return selected_pokemon

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if y >= start_y and y < start_y + visible_pokemon * pokemon_height:
                        index = (y - start_y) // pokemon_height + scroll_offset
                        if index < len(available_pokemon):
                            current_selection = index
                            if is_battle_select:
                                pokemon = available_pokemon[index]
                                if not pokemon.is_fainted():
                                    select_sound.play()
                                    return pokemon
                            elif not is_pokedex:
                                pokemon = available_pokemon[index]
                                if pokemon not in selected_pokemon:
                                    selected_pokemon.append(pokemon)
                                    select_sound.play()
                                    if len(selected_pokemon) >= MAX_PLAYER_POKEMON:
                                        return selected_pokemon
                
                elif event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
                    if y >= start_y and y < start_y + visible_pokemon * pokemon_height:
                        index = (y - start_y) // pokemon_height + scroll_offset
                        if index < len(available_pokemon) and index != current_selection:
                            current_selection = index
                            hover_sound.play()
                
                elif event.type == pygame.MOUSEWHEEL:
                    # Circular scrolling with mouse
                    new_scroll = scroll_offset - event.y
                    if new_scroll < 0:
                        if scroll_offset == 0:  
                            scroll_offset = max(0, len(available_pokemon) - visible_pokemon)
                        else:
                            scroll_offset = max(0, new_scroll)
                    elif new_scroll > len(available_pokemon) - visible_pokemon:
                        if scroll_offset == len(available_pokemon) - visible_pokemon:  
                            scroll_offset = 0
                        else:
                            scroll_offset = min(new_scroll, len(available_pokemon) - visible_pokemon)
                    else:
                        scroll_offset = new_scroll
            
            self.screen.blit(background, (0, 0))
            
            title_surface = title_font.render(title, True, BRIGHT_YELLOW)
            title_rect = title_surface.get_rect()
            title_rect.centerx = (WINDOW_WIDTH//3) + 10
            title_rect.centery = 65 
            self.screen.blit(title_surface, title_rect)
            
            # Draw Pokemon list
            for i in range(visible_pokemon):
                index = i + scroll_offset
                if index >= len(available_pokemon):
                    break  
                    
                pokemon = available_pokemon[index]
                y = start_y + i * pokemon_height
                box_x = ((WINDOW_WIDTH - box_width) // 2) - box_x_offset
                
                # Draw selection box (including fainted Pokemon)
                box_surface = pygame.Surface((box_width, pokemon_height - 10), pygame.SRCALPHA)
                if pokemon.is_fainted():
                    box_color = (*BUTTON_BLACK[:3], 80)  # Greyed out for fainted Pokemon
                elif index == current_selection:
                    box_color = (*BUTTON_BLACK[:3], 180)
                else:
                    box_color = (*BUTTON_BLACK[:3], 150 if pokemon in selected_pokemon else 100)
                pygame.draw.rect(box_surface, box_color, box_surface.get_rect(), border_radius=15)
                self.screen.blit(box_surface, (box_x, y))
                
                border_color = BRIGHT_YELLOW if pokemon in selected_pokemon or index == current_selection else BLACK
                border_width = 3 if index == current_selection else 2
                pygame.draw.rect(self.screen, border_color, 
                               (box_x, y, box_width, pokemon_height - 10), 
                               border_width, border_radius=15)
                
                sprite = pygame.transform.scale(pokemon.sprite, 
                    (int(pokemon.sprite.get_width() * 1.3), int(pokemon.sprite.get_height() * 1.3)))
                sprite_rect = sprite.get_rect(
                    center=(box_x + 100, y + pokemon_height//2))
                self.screen.blit(sprite, sprite_rect)
                
                # Draw Pokemon info 
                info_x = box_x + 200
                name = info_font.render(pokemon.name, True, BRIGHT_YELLOW)
                
                # Draw HP info with current/max values
                hp_text = f"HP: {pokemon.current_hp}/{pokemon.stats['hp']}"
                hp_color = (50, 205, 50) if pokemon.current_hp > 0 else (255, 0, 0)  # Green if alive, red if fainted
                hp_info = info_font.render(hp_text, True, hp_color)
                
                # Draw attack info
                atk_info = info_font.render(f"ATK: {pokemon.stats['attack']}", True, BRIGHT_YELLOW)
                
                self.screen.blit(name, (info_x, y + 20))
                self.screen.blit(hp_info, (info_x, y + 45))
                self.screen.blit(atk_info, (info_x + 200, y + 45))
                
                # Add FAINTED message 
                if pokemon.is_fainted():
                    fainted_text = info_font.render("FAINTED", True, (255, 0, 0))  
                    self.screen.blit(fainted_text, (info_x + 300, y + 35))
            
            if scroll_offset > 0:
                pygame.draw.polygon(self.screen, BLACK,
                                 [(WINDOW_WIDTH - 30, start_y + 27),  
                                  (WINDOW_WIDTH - 20, start_y + 47),  
                                  (WINDOW_WIDTH - 40, start_y + 47)])  
            if scroll_offset < len(available_pokemon) - visible_pokemon:
                end_y = start_y + (visible_pokemon * pokemon_height)
                pygame.draw.polygon(self.screen, BLACK,
                                 [(WINDOW_WIDTH - 30, end_y + 17),  
                                  (WINDOW_WIDTH - 20, end_y - 3),   
                                  (WINDOW_WIDTH - 40, end_y - 3)])  
            
            if is_battle_select:
                esc_text = info_font.render("Press Esc to quit the game", True, BRIGHT_YELLOW)
            else:
                esc_text = info_font.render("Press Esc to return to Main Menu", True, BRIGHT_YELLOW)
            esc_rect = esc_text.get_rect(center=(WINDOW_WIDTH//2 - 15, WINDOW_HEIGHT - 20))
            self.screen.blit(esc_text, esc_rect)
            
            pygame.display.flip()
            self.clock.tick(FPS)
            
    def select_battle_pokemon(self, available_pokemon):
        selected = self.pokemon_selection_menu(available_pokemon, is_battle_select=True)
        if selected is None:  
            self.game.show_game_over_screen() 
            return None
        return selected
        
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'
                    
                for button_name, button in self.buttons.items():
                    if button.handle_event(event):
                        if button_name == 'quit':
                            return 'quit'
                        elif button_name == 'new_game':
                            player_name = self.get_player_name()
                            if player_name:
                                return ('new_game', player_name)
                        elif button_name == 'continue':
                            player_name = self.get_player_name()
                            if player_name and load_player_pokedex(player_name, self.pokemons_data):
                                return ('continue', player_name)
            
            self.draw()
            self.clock.tick(FPS) 