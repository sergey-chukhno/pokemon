import pygame
import requests
from urllib.request import urlopen
import io

class Pokemon(pygame.sprite.Sprite):
    def __init__(self, name, level, x, y):
        super().__init__()
        self.name = name
        self.level = level
        self.x = x
        self.y = y
        
        url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
        self.json = requests.get(url).json()
        
        # Initialize HP, attack, and defense using real stats
        self.max_hp = self.calculate_stat('hp')
        self.current_hp = self.max_hp
        self.attack = self.calculate_stat('attack')
        self.defense = self.calculate_stat('defense')
        
        self.size = 150
        self.set_sprite('front_default')
        self.attacks = self.json['moves'][:4]
        self.types = [type_data['type']['name'] for type_data in self.json['types']]

    def calculate_stat(self, stat_name):
        base_stat = next(stat['base_stat'] for stat in self.json['stats'] if stat['stat']['name'] == stat_name)
        return int(((2 * base_stat + 31 + (252 / 4)) * self.level / 100) + 10 + self.level)

    def set_sprite(self, sprite_type, scale=2.0):
        """Set the sprite image for the Pokemon"""
        if sprite_type == 'back_default':
            image_url = self.json['sprites']['back_default']
        else:
            image_url = self.json['sprites']['front_default']
            
        image_stream = urlopen(image_url).read()
        image_file = io.BytesIO(image_stream)
        self.image = pygame.image.load(image_file).convert_alpha()
        
        # Scale the image
        new_width = int(self.image.get_width() * scale)
        new_height = int(self.image.get_height() * scale)
        self.image = pygame.transform.scale(self.image, (new_width, new_height))
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def set_back_sprite(self, scale=2.0):
        """Set the back view sprite of the Pokemon"""
        self.set_sprite('back_default', scale)

    def draw(self, screen, alpha=255):
        """Draw the Pokemon on the screen"""
        if hasattr(self, 'image'):
            self.image.set_alpha(alpha)
            screen.blit(self.image, (self.x, self.y))

    def draw_hp_bar(self, screen, font, font_small, x, y, green, red, grey, black):
        bar_width = 200  
        bar_height = 25 
        hp_percentage = self.current_hp / self.max_hp
        
        # Fond de la barre
        pygame.draw.rect(screen, grey, (x, y, bar_width, bar_height))
        
        # Couleur de la barre (vert ou rouge)
        hp_color = green if hp_percentage > 0.5 else red
        pygame.draw.rect(screen, hp_color, (x, y, int(bar_width * hp_percentage), bar_height))
        
        # Bordure
        pygame.draw.rect(screen, black, (x, y, bar_width, bar_height), 2)

        hp_label = font_small.render("HP", True, black)
        screen.blit(hp_label, (x - 40, y + 5))

        hp_text = font.render(f"{self.current_hp}/{self.max_hp}", True, black)
        screen.blit(hp_text, (x + bar_width + 10, y))

    def calculate_damage(self, move, target):
        attack_info = requests.get(f"https://pokeapi.co/api/v2/move/{move['move']['name'].lower()}").json()
        
        power = attack_info.get('power', 50)
        if power is None:
            power = 50
            
        damage = round((2 * self.level + 10) / 250 * (self.attack / target.defense) * power + 2)
        
        return max(1, damage)

    def click(self, pos):
        return self.rect.collidepoint(pos)
