import pygame
import random
import os
import math
from config import *
from models.menu import Button
from PIL import Image

class BattleSystem:
    # Class variable to store bag items across all battles
    bag_items = [
        {'name': 'Alarm', 'quantity': 1, 'description': 'Cancels asleep state', 'image': 'alarm.png'},
        {'name': 'Antidote', 'quantity': 2, 'description': 'Cancels poison state', 'image': 'antidote.png'},
        {'name': 'Heater', 'quantity': 1, 'description': 'Cancels freeze state', 'image': 'heater.png'},
        {'name': 'Pokeball', 'quantity': 3, 'description': 'Allows to catch a wild Pokemon', 'image': 'pokeball.png'},
        {'name': 'Potion', 'quantity': 2, 'description': 'Allows to restore HP', 'image': 'potion.png'},
        {'name': 'Suncream', 'quantity': 2, 'description': 'Allows to cure sun burn', 'image': 'suncream.png'}
    ]

    def __init__(self, screen, player_pokemon, enemy_pokemon):
        self.screen = screen
        self.player_pokemon = player_pokemon
        self.enemy_pokemon = enemy_pokemon
        self.current_turn = 'player'  
        self.battle_state = 'main'  
        self.message_log = []
        self.all_player_pokemon = []  
        self.battle_started = False 
        
        # Load and set background based on enemy Pokemon type
        self.background = self.select_background()
        self.background = pygame.transform.scale(self.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        self.setup_battle_ui()
        
        # Add animation variables
        self.animation_time = 0
        self.animation_speed = 1.2  
        self.float_amplitude = 5  
        
        self.load_attack_animations()
        
        # Shake and flash variables
        self.shake_offset = 0
        self.is_shaking = False
        self.shake_frames = 0
        self.shake_target = None
        self.flash_alpha = 0
        
        # Attack sounds
        self.attack_sounds = {
            'normal': pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'attacks/normal.mp3')),
            'fire': pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'attacks/fire.mp3')),
            'water': pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'attacks/water.mp3')),
            'electric': pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'attacks/electric.mp3'))
        }
        
        # Impact sound
        self.impact_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'attacks/impact.mp3'))
        
        for sound in self.attack_sounds.values():
            sound.set_volume(0.3)
        self.impact_sound.set_volume(0.4)  
        
        # State effect definitions
        self.state_effects = {
            'poison': {
                'damage_per_turn': lambda pokemon: pokemon.stats['hp'] // 8,
                'duration': None,  
                'can_attack': True,
                'message': '{pokemon} is hurt by poison!'
            },
            'burn': {
                'damage_per_turn': lambda pokemon: pokemon.stats['hp'] // 16,
                'duration': None,  
                'can_attack': True,
                'message': '{pokemon} is hurt by its burn!'
            },
            'freeze': {
                'duration': 3,
                'can_attack': False,
                'message': '{pokemon} is frozen solid!'
            },
            'asleep': {
                'duration': 3,
                'can_attack': False,
                'message': '{pokemon} is fast asleep!'
            }
        }
        
        # Add state chances to move types
        self.move_state_effects = {
            'tackle': {'state': 'burn', 'chance': 0.95},      # 95% chance to burn
            'scratch': {'state': 'poison', 'chance': 0.95},   # 95% chance to poison
            'pound': {'state': 'freeze', 'chance': 0.95},     # 95% chance to freeze
            'quick attack': {'state': 'asleep', 'chance': 0.95}, # 95% chance to sleep
            
            'ember': {'state': 'burn', 'chance': 0.1},
            'flamethrower': {'state': 'burn', 'chance': 0.3},
            'fire blast': {'state': 'burn', 'chance': 0.4},
            
            'toxic': {'state': 'poison', 'chance': 0.75},
            'poison sting': {'state': 'poison', 'chance': 0.2},
            
            'ice beam': {'state': 'freeze', 'chance': 0.1},
            'blizzard': {'state': 'freeze', 'chance': 0.2},
            
            'hypnosis': {'state': 'asleep', 'chance': 0.6},
            'sleep powder': {'state': 'asleep', 'chance': 0.7},
        }
        
    def select_background(self):
        # Get enemy Pokemon's first type
        pokemon_type = self.enemy_pokemon.types[0]
        
        # Map Pokemon types to backgrounds
        background_mapping = {
            'ground': 'cave.png',
            'rock': 'cave.png',
            'fighting': 'cave.png',
            'grass': 'grass.png',
            'bug': 'grass.png',
            'normal': 'grass.png',
            'water': 'water.png',
            'ice': 'water.png',
            'dragon': 'gym.png',
            'psychic': 'gym.png',
            'electric': 'gym.png',
            'fire': 'gym.png',
            'fairy': 'gym.png',
            'ghost': 'gym.png',
            'dark': 'gym.png',
            'steel': 'gym.png',
            'poison': 'gym.png',
            'flying': 'grass.png'  
        }
        
        # Default to grass background
        bg_file = background_mapping.get(pokemon_type, 'grass.png')
        
        # Load and return background image
        return pygame.image.load(os.path.join(BATTLE_IMAGES_DIR, bg_file))
        
    def setup_battle_ui(self):
        # Battle command buttons 
        button_width = int(WINDOW_WIDTH * 0.45 / 2) - 15  
        button_height = 50
        button_y = WINDOW_HEIGHT - button_height - 10
        button_x_start = WINDOW_WIDTH - (WINDOW_WIDTH * 0.45) + 10  
        
        self.command_buttons = {
            'fight': Button(button_x_start, button_y,
                          button_width, button_height, "Fight", GREEN, (150, 255, 150)),
            'bag': Button(button_x_start + button_width + 10, button_y,
                         button_width, button_height, "Bag", BLUE, (150, 150, 255)),
            'pokemon': Button(button_x_start, button_y - button_height - 5,
                            button_width, button_height, "Pokemon", RED, (255, 150, 150)),
            'run': Button(button_x_start + button_width + 10, button_y - button_height - 5,
                         button_width, button_height, "Run", (200, 200, 200), (150, 150, 150))
        }
        
        for button in self.command_buttons.values():
            try:
                button.font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 20) 
            except:
                button.font = pygame.font.Font(None, 20)
        
        self.move_buttons = {}
        for i, move in enumerate(self.player_pokemon.moves):
            x = button_x_start if i < 2 else button_x_start + button_width + 10
            y = button_y if i % 2 == 0 else button_y - button_height - 5
            self.move_buttons[move] = Button(x, y, button_width, button_height,
                                           move.capitalize(), BLUE, (150, 150, 255))
            try:
                self.move_buttons[move].font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 20)
            except:
                self.move_buttons[move].font = pygame.font.Font(None, 20)
    
    def setup_pokemon_switch_ui(self):
        button_width = WINDOW_WIDTH // 3
        button_height = 50
        self.pokemon_switch_buttons = {}
        
        for i, pokemon in enumerate(self.all_player_pokemon):
            x = (WINDOW_WIDTH - button_width) // 2
            y = 200 + i * (button_height + 10)
            
            button = Button(x, y, button_width, button_height,
                f"{pokemon.name} (HP: {pokemon.current_hp}/{pokemon.stats['hp']})",
                BLUE, (150, 150, 255)
            )
            
            try:
                button.font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 16)  # Reduced font size
            except:
                button.font = pygame.font.Font(None, 16)
            

            sprite_size = button_height - 10  
            button.pokemon_sprite = pygame.transform.scale(pokemon.sprite, (sprite_size, sprite_size))
            
            def custom_draw(button, screen):
                button_surface = pygame.Surface((button.rect.width, button.rect.height), pygame.SRCALPHA)
                pygame.draw.rect(button_surface, BUTTON_BLACK, button_surface.get_rect(), border_radius=15)
                screen.blit(button_surface, button.rect)
                
                border_color = BRIGHT_YELLOW if button.is_hovered else BLACK
                border_width = 3 if button.is_hovered else 2
                pygame.draw.rect(screen, border_color, button.rect, border_width, border_radius=15)
                

                sprite_x = button.rect.x + 5
                sprite_y = button.rect.y + (button.rect.height - sprite_size) // 2
                screen.blit(button.pokemon_sprite, (sprite_x, sprite_y))
                
                text_surface = button.font.render(button.text, True, BRIGHT_YELLOW)
                text_rect = text_surface.get_rect()
                text_rect.centerx = button.rect.centerx + sprite_size//2 
                text_rect.centery = button.rect.centery
                screen.blit(text_surface, text_rect)
            
            button.custom_draw = lambda screen, btn=button: custom_draw(btn, screen)
            
            self.pokemon_switch_buttons[pokemon] = button
    
    def draw_hp_box(self, pokemon, x, y, is_player):
        box_width = 200
        box_height = 80
        
        hp_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(hp_surface, (200, 200, 200, 180), hp_surface.get_rect(), border_radius=15)  
        self.screen.blit(hp_surface, (x, y))
        
        font = pygame.font.Font(None, 24)
        
        name_text = font.render(pokemon.name, True, BLACK)
        self.screen.blit(name_text, (x + 10, y + 5))
        
        level_text = font.render(f"Lv.{pokemon.level}", True, BLACK)
        self.screen.blit(level_text, (x + box_width - 60, y + 5))
        
        hp_percent = pokemon.current_hp / pokemon.stats['hp']
        bar_width = 180
        bar_height = 10
        bar_x = x + 10
        bar_y = y + 35
        
        pygame.draw.rect(self.screen, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)
        hp_color = GREEN if hp_percent > 0.5 else YELLOW if hp_percent > 0.2 else RED
        pygame.draw.rect(self.screen, hp_color,
                        (bar_x + 1, bar_y + 1, int(bar_width * hp_percent), bar_height - 2))
        
        hp_text = font.render(f"{pokemon.current_hp}/{pokemon.stats['hp']}", True, BLACK)
        self.screen.blit(hp_text, (x + 10, y + 45))
        
        # Experience (only for player's Pokemon)
        if is_player:
            exp_text = font.render(f"EXP: {pokemon.experience}/{pokemon.level * 100}", True, BLACK)
            self.screen.blit(exp_text, (x + 10, y + 65))
        
        # Draw state icon if Pokemon has a state
        if pokemon.state:
            icon = pokemon.state_icons[pokemon.state]
            icon_x = x + 174  
            icon_y = y + 1   
            self.screen.blit(icon, (icon_x, icon_y))
    
    def draw_message_log(self):
        log_width = int(WINDOW_WIDTH * 0.55) - 20  
        log_height = 100
        log_x = 10
        log_y = WINDOW_HEIGHT - log_height - 10
        
        log_surface = pygame.Surface((log_width, log_height), pygame.SRCALPHA)
        pygame.draw.rect(log_surface, (255, 255, 255, 255), log_surface.get_rect(), border_radius=15)
        self.screen.blit(log_surface, (log_x, log_y))
        
        font = pygame.font.Font(None, 24)
        for i, message in enumerate(self.message_log[-4:]): 
            text = font.render(message, True, BLACK)
            self.screen.blit(text, (log_x + 10, log_y + 10 + i * 25))
    
    def add_message(self, message):
        self.message_log.append(message)
        
    def calculate_damage(self, attacker, defender, move):
        base_damage = attacker.stats['attack'] // 5
        damage = random.randint(base_damage - 5, base_damage + 5)
        return max(1, damage)
        
    def load_attack_animations(self):
        # Debug: Print current directory and full path
        print(f"Current working directory: {os.getcwd()}")
        print(f"BATTLE_ATTACKS_DIR: {BATTLE_ATTACKS_DIR}")
        print(f"Directory exists: {os.path.exists(BATTLE_ATTACKS_DIR)}")
        print(f"Directory contents: {os.listdir(BATTLE_ATTACKS_DIR) if os.path.exists(BATTLE_ATTACKS_DIR) else 'Directory not found'}")
        
        self.attack_frames = {}
        attack_types = ['normal', 'fire', 'water', 'electric']
        
        for attack_type in attack_types:
            gif_path = os.path.join(BATTLE_ATTACKS_DIR, f'{attack_type}.gif')
            print(f"Trying to load: {gif_path}")
            print(f"File exists: {os.path.exists(gif_path)}")
            try:
                frames = []
                with Image.open(gif_path) as gif:
                    for frame_idx in range(gif.n_frames):
                        gif.seek(frame_idx)
                        frame_str = gif.convert('RGBA').tobytes()
                        frame_surf = pygame.image.fromstring(
                            frame_str, gif.size, 'RGBA')
                        frames.append(frame_surf)
                self.attack_frames[attack_type] = frames
            except Exception as e:
                print(f"Error loading {attack_type}.gif: {e}")
                print(f"Tried to load from: {gif_path}")
                self.attack_frames[attack_type] = []
                
    def get_move_type(self, move):
        # Convert move name to lowercase and replace hyphens with spaces
        move = move.lower().strip().replace('-', ' ')
        
        move_types = {
            # Normal moves
            'tackle': 'normal',
            'scratch': 'normal',
            'pound': 'normal',
            'quick attack': 'normal',
            'slam': 'normal',
            'cut': 'normal',
            'double kick': 'normal',
            
            # Fire moves
            'ember': 'fire',
            'flamethrower': 'fire',
            'fire blast': 'fire',
            'fire punch': 'fire',
            'flame wheel': 'fire',
            
            # Water moves
            'water gun': 'water',
            'bubble': 'water',
            'hydro pump': 'water',
            'surf': 'water',
            'waterfall': 'water',
            'aqua jet': 'water',
            
            # Electric moves
            'thundershock': 'electric',
            'thunderbolt': 'electric',
            'thunder': 'electric',
            'thunder punch': 'electric',  
            'spark': 'electric',
            'thunder wave': 'electric',
            'volt tackle': 'electric'
        }
        
        move_type = move_types.get(move, 'normal')
        print(f"Move: '{move}' (original: '{move}'), Type: {move_type}")  
        
        # Verify animation exists
        if move_type in self.attack_frames:
            if not self.attack_frames[move_type]:
                print(f"Warning: No frames loaded for {move_type} type")
                return 'normal'
        else:
            print(f"Warning: No animation found for {move_type} type")
            return 'normal'
            
        return move_type
        
    def apply_state_effects(self, pokemon):
        if not pokemon.state:
            return True
            
        effect = self.state_effects[pokemon.state]
        
        # Apply damage for poison/burn
        if 'damage_per_turn' in effect:
            damage = effect['damage_per_turn'](pokemon)
            pokemon.take_damage(damage)
            self.add_message(effect['message'].format(pokemon=pokemon.name))
        
        # Handle duration-based states
        if effect['duration']:
            pokemon.state_duration += 1
            if pokemon.state_duration >= effect['duration']:
                pokemon.state = None
                pokemon.state_duration = 0
                self.add_message(f"{pokemon.name} recovered from {pokemon.state}!")
        
        return effect['can_attack']

    def handle_attack(self, attacker, defender, move):
        # Check if Pokemon can attack based on state
        if not self.apply_state_effects(attacker):
            self.add_message(self.state_effects[attacker.state]['message'].format(
                pokemon=attacker.name))
            return False
            
        attack_type = self.get_move_type(move)
        print(f"Executing attack animation for type: {attack_type}")
        
        if attack_type in self.attack_frames and self.attack_frames[attack_type]:
            frames = self.attack_frames[attack_type]
            
            if attack_type in self.attack_sounds:
                try:
                    pygame.mixer.stop()  
                    self.attack_sounds[attack_type].play()
                    print(f"Playing {attack_type} sound")
                except Exception as e:
                    print(f"Error playing sound: {e}")
            
            if attacker == self.player_pokemon:
                start_x = 180
                start_y = WINDOW_HEIGHT//2 + 30
                end_x = WINDOW_WIDTH - 280
                end_y = WINDOW_HEIGHT//4 + 30
                is_defender_player = False
            else:
                start_x = WINDOW_WIDTH - 280
                start_y = WINDOW_HEIGHT//4 + 30
                end_x = 180
                end_y = WINDOW_HEIGHT//2 + 30
                is_defender_player = True
            
            for frame_idx in range(len(frames)):
                self.draw()
                
                for element in range(5):
                    element_progress = (frame_idx / (len(frames) - 1)) - (element * 0.15)
                    if 0 <= element_progress <= 1:
                        frame = frames[frame_idx % len(frames)]
                        size = 70
                        scaled_frame = pygame.transform.scale(frame, (size, size))
                        
                        x = start_x + (end_x - start_x) * element_progress
                        y = start_y + (end_y - start_y) * element_progress
                        
                        self.screen.blit(scaled_frame, (x - size//2, y - size//2))
                
                pygame.display.flip()
                pygame.time.Clock().tick(300)
            
            # Add shake and flash effect when attack hits
            self.shake_and_flash_pokemon(is_defender_player)
        
        # Calculate and apply damage
        damage = self.calculate_damage(attacker, defender, move)
        defender.take_damage(damage)
        self.add_message(f"{attacker.name} used {move}!")
        self.add_message(f"{defender.name} took {damage} damage!")
        
        # Check for state effects
        move_lower = move.lower().strip().replace('-', ' ')
        if move_lower in self.move_state_effects:
            effect = self.move_state_effects[move_lower]
            if random.random() < effect['chance']:
                defender.state = effect['state']
                defender.state_duration = 0
                self.add_message(f"{defender.name} was {effect['state']}!")
        
        if defender.is_fainted():
            self.add_message(f"{defender.name} fainted!")
            return True
        return False
        
    def handle_enemy_turn(self):
        move = random.choice(self.enemy_pokemon.moves)
        return self.handle_attack(self.enemy_pokemon, self.player_pokemon, move)
        
    def shake_and_flash_pokemon(self, is_player):
        self.shake_frames = 10
        self.shake_target = 'player' if is_player else 'enemy'
        self.is_shaking = True
        self.flash_alpha = 180
        
        try:
            impact_channel = pygame.mixer.Channel(1) 
            impact_channel.play(self.impact_sound)
        except Exception as e:
            print(f"Error playing impact sound: {e}")

    def draw(self):
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Update animation time
        self.animation_time += 0.1
        
        # Calculate floating offset 
        float_offset = self.float_amplitude * math.sin(self.animation_time * self.animation_speed)
        
        # Update shake animation if active
        if self.is_shaking:
            self.shake_offset = 10 if (self.shake_frames % 2) == 0 else -10
            self.shake_frames -= 1
            if self.shake_frames <= 0:
                self.is_shaking = False
                self.shake_offset = 0
                self.flash_alpha = 0
            
        # Draw Pokemon sprites with animation
        player_pos = (100, WINDOW_HEIGHT//2 + float_offset)
        enemy_pos = (WINDOW_WIDTH - 200, WINDOW_HEIGHT//4 - float_offset)
        
        # Apply shake offset if shaking
        if self.is_shaking:
            if self.shake_target == 'player':
                player_pos = (player_pos[0] + self.shake_offset, player_pos[1])
            else:
                enemy_pos = (enemy_pos[0] + self.shake_offset, enemy_pos[1])
        
        scaled_player_sprite = pygame.transform.scale(self.player_pokemon.sprite, 
            (int(self.player_pokemon.sprite.get_width() * 2.0), 
             int(self.player_pokemon.sprite.get_height() * 2.0)))
        flipped_sprite = pygame.transform.flip(scaled_player_sprite, True, False)
        
        scaled_enemy_sprite = pygame.transform.scale(self.enemy_pokemon.sprite,
            (int(self.enemy_pokemon.sprite.get_width() * 2.0),
             int(self.enemy_pokemon.sprite.get_height() * 2.0)))
        
        # Apply red tint to the hit Pokemon
        if self.is_shaking and self.flash_alpha > 0:
            if self.shake_target == 'player':
                tinted_sprite = flipped_sprite.copy()
                tinted_sprite.fill((255, 0, 0, self.flash_alpha), special_flags=pygame.BLEND_RGBA_MULT)
                self.screen.blit(tinted_sprite, player_pos)
            else:
                tinted_sprite = scaled_enemy_sprite.copy()
                tinted_sprite.fill((255, 0, 0, self.flash_alpha), special_flags=pygame.BLEND_RGBA_MULT)
                self.screen.blit(tinted_sprite, enemy_pos)
            self.flash_alpha = max(0, self.flash_alpha - 20)  # Fade out the flash
        else:
            self.screen.blit(flipped_sprite, player_pos)
            self.screen.blit(scaled_enemy_sprite, enemy_pos)
        
        self.draw_hp_box(self.player_pokemon, player_pos[0], player_pos[1] - 120, True)
        self.draw_hp_box(self.enemy_pokemon, enemy_pos[0] - 25, enemy_pos[1] - 120, False)
        
        self.draw_message_log()
        
        # Draw buttons based on battle state
        if self.battle_state == 'main':
            for button in self.command_buttons.values():
                button.draw(self.screen)
        elif self.battle_state == 'fight':
            for button in self.move_buttons.values():
                button.draw(self.screen)
        elif self.battle_state == 'pokemon':
            for button in self.pokemon_switch_buttons.values():
                button.draw(self.screen)
        
        pygame.display.flip()
        
    def handle_events(self, event):
    
        if event.type == pygame.MOUSEMOTION:
            # Update hover state for all buttons
            for button in self.command_buttons.values():
                button.handle_event(event)
            for button in self.move_buttons.values():
                button.handle_event(event)
            if self.battle_state == 'pokemon':
                for button in self.pokemon_switch_buttons.values():
                    button.handle_event(event)
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.battle_state == 'main':
                for action, button in self.command_buttons.items():
                    if button.rect.collidepoint(event.pos):
                        if action == 'fight':
                            self.battle_started = True  
                            self.battle_state = 'fight'
                            return 'continue'
                        elif action == 'bag':
                            self.battle_state = 'bag'
                            return self.handle_bag()
                        elif action == 'pokemon':
                            self.battle_state = 'pokemon'
                            self.setup_pokemon_switch_ui()
                            return 'continue'
                        elif action == 'run':
                            if not self.battle_started:
                                self.add_message(f"{self.player_pokemon.name} chose to run away!")
                                return 'run'
                            else:
                                self.add_message(f"Too late. {self.player_pokemon.name} cannot run!")
                                return 'continue'
                            
            elif self.battle_state == 'fight':
                for move, button in self.move_buttons.items():
                    if button.rect.collidepoint(event.pos):
                        if self.handle_attack(self.player_pokemon, self.enemy_pokemon, move):
                            return 'victory'
                            
                        if self.handle_enemy_turn():
                            return 'defeat'
                            
                        self.battle_state = 'main'
                        return 'continue'
            
            elif self.battle_state == 'pokemon':
                for pokemon, button in self.pokemon_switch_buttons.items():
                    if button.rect.collidepoint(event.pos):
                        if pokemon != self.player_pokemon and not pokemon.is_fainted():
                            self.player_pokemon = pokemon
                            self.battle_state = 'main'
                            self.add_message(f"Go, {pokemon.name}!")
                            self.battle_started = True  
                            
                            # Enemy gets a free attack when switching
                            if self.handle_enemy_turn():
                                return 'defeat'
                            
                            return 'continue'
        
        return 'continue'
        
    def run(self):
        self.add_message(f"A wild {self.enemy_pokemon.name} appeared! What {self.player_pokemon.name} will do?")
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'
                
                result = self.handle_events(event)
                if result != 'continue':
                    return result
            
            self.draw()
            pygame.time.Clock().tick(FPS)

    def show_bag_menu(self):
        running = True
        selected_index = 0
        
        # Create a static background by taking a snapshot of the current battle scene
        background = self.screen.copy()
        
        while running:
            # Use the static background instead of continuously drawing the battle scene
            self.screen.blit(background, (0, 0))
            
            menu_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(menu_surface, (0, 0, 0, 128), menu_surface.get_rect())
            self.screen.blit(menu_surface, (0, 0))
            
            mouse_pos = pygame.mouse.get_pos()
            
            for i, item in enumerate(self.bag_items):
                box_x = 50
                box_y = 50 + i * 70
                box_width = WINDOW_WIDTH - 100
                box_height = 60
                
                item_rect = pygame.Rect(box_x, box_y, box_width, box_height)
                if item_rect.collidepoint(mouse_pos):
                    selected_index = i
                
                # Draw box with list of items
                box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
                color = (255, 255, 255, 230) if i == selected_index else (200, 200, 200, 200)
                pygame.draw.rect(box_surface, color, box_surface.get_rect(), border_radius=10)
                self.screen.blit(box_surface, (box_x, box_y))
                
                # Draw item image
                try:
                    item_image = pygame.image.load(os.path.join(BATTLE_IMAGES_DIR, 'bag', item['image']))
                    item_image = pygame.transform.scale(item_image, (32, 32))
                    self.screen.blit(item_image, (box_x + 10, box_y + 14))
                except:
                    print(f"Could not load image: {item['image']}")
                
                # Draw item name and quantity with Pokemon font
                try:
                    font = pygame.font.Font(os.path.join(FONTS_DIR, "pokemonsolid.ttf"), 20)
                except:
                    font = pygame.font.Font(None, 24)
                name_text = font.render(f"{item['name']} x{item['quantity']}", True, BLACK)
                self.screen.blit(name_text, (box_x + 50, box_y + 10))
                
                # Draw description
                desc_font = pygame.font.Font(None, 20)
                desc_text = desc_font.render(item['description'], True, BLACK)
                self.screen.blit(desc_text, (box_x + 50, box_y + 35))
            
            hint_font = pygame.font.Font(None, 24)
            hint_text = hint_font.render("Press ENTER to use item, ESC to cancel", True, WHITE)
            hint_rect = hint_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 30))
            self.screen.blit(hint_text, hint_rect)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.battle_state = 'main'
                        return None
                    elif event.key == pygame.K_RETURN:
                        selected_item = self.bag_items[selected_index]
                        if selected_item['quantity'] > 0:
                            return selected_item
                    elif event.key == pygame.K_UP:
                        selected_index = (selected_index - 1) % len(self.bag_items)
                    elif event.key == pygame.K_DOWN:
                        selected_index = (selected_index + 1) % len(self.bag_items)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        selected_item = self.bag_items[selected_index]
                        if selected_item['quantity'] > 0:
                            return selected_item
            
            pygame.time.Clock().tick(60)
        
        return None

    def handle_bag(self):
        selected_item = self.show_bag_menu()
        if selected_item:
            if selected_item['name'] == 'Alarm':
                if self.player_pokemon.state == 'asleep':
                    self.player_pokemon.state = None
                    self.player_pokemon.state_duration = 0
                    self.add_message(f"{self.player_pokemon.name} woke up!")
                else:
                    self.add_message(f"{self.player_pokemon.name} is not asleep!")
                selected_item['quantity'] -= 1
            elif selected_item['name'] == 'Antidote':
                if self.player_pokemon.state == 'poison':
                    self.player_pokemon.state = None
                    self.player_pokemon.state_duration = 0
                    self.add_message(f"{self.player_pokemon.name} was cured of poison!")
                else:
                    self.add_message(f"{self.player_pokemon.name} is not poisoned!")
                selected_item['quantity'] -= 1
            elif selected_item['name'] == 'Heater':
                if self.player_pokemon.state == 'freeze':
                    self.player_pokemon.state = None
                    self.player_pokemon.state_duration = 0
                    self.add_message(f"{self.player_pokemon.name} was thawed out!")
                else:
                    self.add_message(f"{self.player_pokemon.name} is not frozen!")
                selected_item['quantity'] -= 1
            elif selected_item['name'] == 'Suncream':
                if self.player_pokemon.state == 'burn':
                    self.player_pokemon.state = None
                    self.player_pokemon.state_duration = 0
                    self.add_message(f"{self.player_pokemon.name} was cured of burn!")
                else:
                    self.add_message(f"{self.player_pokemon.name} is not burnt!")
                selected_item['quantity'] -= 1
            elif selected_item['name'] == 'Potion':
                self.player_pokemon.current_hp = self.player_pokemon.stats['hp']  
                self.add_message(f"{self.player_pokemon.name}'s health was restored!")
                selected_item['quantity'] -= 1
            elif selected_item['name'] == 'Pokeball':
                selected_item['quantity'] -= 1
                if random.random() < 0.25:  # 25% chance of success
                    self.enemy_pokemon.current_hp = 0
                    self.add_message(f"Gotcha! {self.enemy_pokemon.name} was caught!")
                    return 'victory'
                else:
                    self.player_pokemon.current_hp = 0
                    self.add_message(f"Oh no! {self.enemy_pokemon.name} broke free!")
                    return 'defeat'
            else:
                self.add_message(f"Used {selected_item['name']}!")
                selected_item['quantity'] -= 1
        self.battle_state = 'main'
        return 'continue' 