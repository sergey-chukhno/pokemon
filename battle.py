import pygame
import random
import requests
import json
from pokemon import Pokemon
from button import Button

url = "https://pokeapi.co/api/v2"
opponent_pokemon = [
    'Pidgey','Rattata','Spearow','Caterpie','Weedle','Pikachu','Sandshrew','Nidoran-m','Nidoran-f','Clefairy','Vulpix','Jigglypuff','Zubat','Oddish'    
]

class Battle:
    def __init__(self, player_pokemon, screen, fonts, images, colors):
        self.screen = screen
        self.font = fonts['font']
        self.font_small = fonts['font_s']
        self.font_poke = fonts['font_poke']
        self.font_poke_small = fonts['font_poke_s']
        self.images = images
        self.colors = colors
        
        self.player_pokemon = player_pokemon
        self.player_pokemon.x = 50 
        self.player_pokemon.y = 275
        self.player_pokemon.set_sprite('back_default', 3)
        
        opponent_name = random.choice(opponent_pokemon)
        self.opponent_pokemon = Pokemon(opponent_name, random.randint(1, 5), 500, 150)
        self.opponent_pokemon.set_sprite('front_default')

        button_width = 200
        button_height = 50

        x = 400
        y = 499

        self.fight_button = pygame.transform.scale(images['fight_button'], (button_width, button_height))
        self.fight_button_rect = self.fight_button.get_rect(topleft=(x, y))

        self.bag_button = pygame.transform.scale(images['bag_button'], (button_width, button_height))
        self.bag_button_rect = self.bag_button.get_rect(topleft=(x + button_width, y))

        self.pokemon_button = pygame.transform.scale(images['pokemon_button'], (button_width, button_height))
        self.pokemon_button_rect = self.pokemon_button.get_rect(topleft=(x, y + button_height))

        self.run_button = pygame.transform.scale(images['run_button'], (button_width, button_height))
        self.run_button_rect = self.run_button.get_rect(topleft=(x + button_width, y + button_height))

        self.show_attacks = False
        self.attack_buttons = []
        
        self.pokedex_show = False
        self.pokedex_pokemon_x = 50
        self.pokedex_pokemon_y = 100
        self.pokedex_pokemon_scale = 1.0  
        self.current_turn = 'player' 
        self.attack_delay = 0 

        self.shake_duration = 500
        self.shake_intensity = 5 
        self.shake_start = 0       
        self.shaking_pokemon = None 
        self.original_player_pos = (50, 275)
        self.original_opponent_pos = (500, 150)

    def draw(self, hovered_attack):
        screen = self.screen
        colors = self.colors
        
        # Fond et arrière-plan
        screen.fill(colors['white'])
        screen.blit(self.images['background'], (0, 0))

        current_time = pygame.time.get_ticks()
        if self.shaking_pokemon and current_time - self.shake_start < self.shake_duration:
            progress = (current_time - self.shake_start) / self.shake_duration
            offset = int(self.shake_intensity * (1 - progress) * (random.random() * 2 - 1))
            
            if self.shaking_pokemon == 'player':
                self.player_pokemon.x = self.original_player_pos[0] + offset
                self.player_pokemon.y = self.original_player_pos[1] + offset
            else:
                self.opponent_pokemon.x = self.original_opponent_pos[0] + offset
                self.opponent_pokemon.y = self.original_opponent_pos[1] + offset
        else:
            # Réinitialiser les positions
            self.shaking_pokemon = None
            self.player_pokemon.x = self.original_player_pos[0]
            self.player_pokemon.y = self.original_player_pos[1]
            self.opponent_pokemon.x = self.original_opponent_pos[0]
            self.opponent_pokemon.y = self.original_opponent_pos[1]

        # Afficher les Pokémon et le reste du contenu
        self.player_pokemon.draw(screen)
        self.opponent_pokemon.draw(screen)

        # Affiche les Pokémon
        self.player_pokemon.draw(screen)
        self.opponent_pokemon.draw(screen)
    
        self.player_pokemon.draw_hp_bar(screen, self.font, self.font_small, 400, 450, colors['green'], colors['red'], colors['grey'], colors['black']) 
        self.opponent_pokemon.draw_hp_bar(screen, self.font, self.font_small, 100, 50, colors['green'], colors['red'], colors['grey'], colors['black'])  
        
        # Affichage des noms et niveaux
        player_name = self.font.render(self.player_pokemon.name, True, colors['black'])
        opponent_name = self.font.render(self.opponent_pokemon.name, True, colors['black'])
        player_level = self.font.render(f"LV: {self.player_pokemon.level}", True, colors['black'])
        opponent_level = self.font.render(f"LV: {self.opponent_pokemon.level}", True, colors['black'])
        
        screen.blit(player_name, (400, 420))
        screen.blit(opponent_name, (100, 20)) 
        screen.blit(player_level, (700, 450)) 
        screen.blit(opponent_level, (400, 50))

        # Mode combat
        if not self.show_attacks and not self.pokedex_show:
            pygame.draw.rect(screen, colors['grey'], (0, 500, 800, 100))
            screen.blit(self.images['button_bar'], (0, 500))
            text = self.font_poke.render(f"What will {self.player_pokemon.name} do ?", True, colors['black'])
            screen.blit(text, (50, 535))
            screen.blit(self.fight_button, self.fight_button_rect)
            screen.blit(self.bag_button, self.bag_button_rect)
            screen.blit(self.pokemon_button, self.pokemon_button_rect)
            screen.blit(self.run_button, self.run_button_rect)
        # Mode attaques
        elif self.show_attacks:
            screen.blit(self.images['attackbox'], (0, 500))
            for button in self.attack_buttons:
                button.draw(screen, self.font_poke, colors['black'])

        # Affichage d'infos sur l'attaque survolée
        if self.show_attacks and hovered_attack:
            attack_info = requests.get(f"{url}/move/{hovered_attack.lower()}").json()
            
            type_ = attack_info['type']['name'].capitalize()
            pp = attack_info.get('pp', 'N/A')
            
            text = self.font_poke.render(type_, True, colors['black'])
            screen.blit(text, (660, 560))
            text = self.font_poke.render(f"{pp}", True, colors['black'])
            screen.blit(text, (665, 520))

        # Mode Pokédex
        if self.pokedex_show:
            screen.fill(colors['white'])
            screen.blit(self.images['background_poke'], (0, 0))
            
            # Charger tous les Pokémon du joueur
            with open("player_pokemon.json", "r") as file:
                all_pokemon = json.load(file)
            
            for i, poke_data in enumerate(all_pokemon[:6]):
                col = i // 3 
                row = i % 3
                
                x_offset = col * 400
                y_offset = row * 150
                
                current_x = self.pokedex_pokemon_x + x_offset
                current_y = self.pokedex_pokemon_y + y_offset

                box_rect = pygame.Rect(current_x +60, current_y - 35, 250, 100)
                mouse_pos = pygame.mouse.get_pos()
                
                temp_pokemon = Pokemon(poke_data['name'], poke_data['level'], current_x + 50, current_y - 50)
                temp_pokemon.current_hp = poke_data['current_hp']
                temp_pokemon.max_hp = poke_data['max_hp']
                
                screen.blit(self.images['podex_box'], (current_x + 60, current_y - 35))
                
                name_text = self.font_poke_small.render(temp_pokemon.name, True, colors['white'])
                screen.blit(name_text, (current_x + 135, current_y - 20))
                
                # Afficher le niveau
                level_text = self.font_poke_small.render(f"Lv {temp_pokemon.level}", True, colors['white'])
                screen.blit(level_text, (current_x + 160, current_y + 5))
                
                # Afficher le texte HP
                hp_text = self.font_poke_small.render("HP:", True, colors['white'])
                screen.blit(hp_text, (current_x + 110, current_y + 30))
                
                # Afficher le sprite du Pokémon
                temp_pokemon.set_sprite('front_default', self.pokedex_pokemon_scale)
                temp_pokemon.draw(screen)
                
                # Dessiner la barre de HP
                bar_width = 100
                bar_height = 10
                x = current_x + 135
                y = current_y + 127
                
                hp_percentage = temp_pokemon.current_hp / temp_pokemon.max_hp
                pygame.draw.rect(screen, colors['grey'], (x, y - 95, bar_width, bar_height))
                hp_color = colors['green'] if hp_percentage > 0.5 else colors['red']
                pygame.draw.rect(screen, hp_color, (x, y - 95, int(bar_width * hp_percentage), bar_height))
                pygame.draw.rect(screen, colors['black'], (x, y - 95, bar_width, bar_height), 2)
                
                hp_numbers = self.font_poke_small.render(
                    f"{temp_pokemon.current_hp}/{temp_pokemon.max_hp}", True, colors['white'])
                screen.blit(hp_numbers, (x + bar_width + 10, y - 97))

        if self.current_turn == 'opponent' and not self.pokedex_show and pygame.time.get_ticks() > self.attack_delay:
            self.enemy_attack()

    def attacks_buttons(self):
        self.attack_buttons = []
        button_width = 200
        button_height = 35
        x = 75
        y = 515
        for i, move in enumerate(self.player_pokemon.attacks):
            btn = Button(x + (i % 2) * button_width, y + (i // 2) * button_height, button_width, button_height, move['move']['name'], self.colors['green'])
            self.attack_buttons.append(btn)

    def handle_attack(self, move_name):
        if self.current_turn == 'player':
            selected_move = next((move for move in self.player_pokemon.attacks if move['move']['name'] == move_name), None)
            if selected_move:
                self.shake_start = pygame.time.get_ticks()
                self.shaking_pokemon = 'opponent'
                damage = self.player_pokemon.calculate_damage(selected_move, self.opponent_pokemon)
                self.opponent_pokemon.current_hp -= damage
                if self.opponent_pokemon.current_hp < 0:
                    self.opponent_pokemon.current_hp = 0
                
                if self.opponent_pokemon.current_hp <= 0:
                    self.handle_pokemon_defeat()
                    self.player_pokemon.level = min(100, self.player_pokemon.level + 1)
                else:
                    self.current_turn = 'opponent'  
                    self.attack_delay = pygame.time.get_ticks() + 1000  

    def enemy_attack(self):
        
        if self.current_turn == 'opponent':
            self.shake_start = pygame.time.get_ticks()
            self.shaking_pokemon = 'player'
            
            enemy_move = random.choice(self.opponent_pokemon.attacks)
            damage = self.opponent_pokemon.calculate_damage(enemy_move, self.player_pokemon)
            self.player_pokemon.current_hp = max(0, self.player_pokemon.current_hp - damage)
            self.current_turn = 'player'  # Change de tour après l'attaque de l'adversaire

    def handle_pokemon_defeat(self):
        self.capture_pokemon()
        self.generate_new_opponent()

    def capture_pokemon(self):
        with open("player_pokemon.json", "r") as file:
            current_pokemon = json.load(file)
            
        pokemon_names = [p["name"] for p in current_pokemon]
        if self.opponent_pokemon.name not in pokemon_names:
            new_pokemon = {
                "name": self.opponent_pokemon.name,
                "level": self.opponent_pokemon.level,
                "current_hp": self.opponent_pokemon.max_hp, 
                "max_hp": self.opponent_pokemon.max_hp,
                "types": self.opponent_pokemon.types,
                "attacks": [move["move"]["name"] for move in self.opponent_pokemon.attacks]
            }
            current_pokemon.append(new_pokemon)
            
            with open("player_pokemon.json", "w") as file:
                json.dump(current_pokemon, file, indent=4)

    def generate_new_opponent(self):
        opponent_name = random.choice(opponent_pokemon)
        self.opponent_pokemon = Pokemon(opponent_name, random.randint(1, 5), 500, 150)
        self.opponent_pokemon.set_sprite('front_default')

    def handle_pokedex_click(self, mouse_pos):
        with open("player_pokemon.json", "r") as file:
            all_pokemon = json.load(file)
        
        for i, poke_data in enumerate(all_pokemon[:6]):
            col = i // 3
            row = i % 3
            
            x_offset = col * 300
            y_offset = row * 150
            
            current_x = self.pokedex_pokemon_x + x_offset
            current_y = self.pokedex_pokemon_y + y_offset

            box_rect = pygame.Rect(current_x, current_y - 35, 250, 100)
            
            if box_rect.collidepoint(mouse_pos):
                selected_pokemon = Pokemon(poke_data['name'], poke_data['level'], 50, 275)  # Update coordinates here
                selected_pokemon.current_hp = poke_data['current_hp']
                selected_pokemon.max_hp = poke_data['max_hp']
                selected_pokemon.types = poke_data['types']
                selected_pokemon.attacks = [{'move': {'name': attack}} for attack in poke_data['attacks']]
                selected_pokemon.set_sprite('back_default', scale=3.0)
                self.player_pokemon = selected_pokemon
                self.pokedex_show = False
                break

