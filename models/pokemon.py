import pygame
import json
from config import *
import os

class Pokemon:
    def __init__(self, pokemon_data):
        self.id = pokemon_data['id']
        self.name = pokemon_data['name'].capitalize()
        self.types = pokemon_data['types']
        self.stats = pokemon_data['stats']
        self.moves = pokemon_data['moves']
        self.current_hp = pokemon_data.get('current_hp', self.stats['hp'])
        
        # Load sprite using relative path
        sprite_path = os.path.join(DATA_DIR, pokemon_data['sprite_path'].replace('\\', '/'))
        try:
            self.sprite = pygame.image.load(sprite_path)
        except FileNotFoundError:
            print(f"Could not load sprite at {sprite_path}")
            # Create a fallback sprite
            self.sprite = pygame.Surface((64, 64))
            self.sprite.fill((255, 0, 255))  # Fill with magenta to make missing sprites obvious
        self.position = None
        self.state = None  # Can be: 'poison', 'burn', 'freeze', 'asleep' or None
        self.state_duration = 0  # For temporary states like sleep
        
        # Load state icons using relative paths
        self.state_icons = {}
        for state in ['poison', 'burn', 'freeze', 'asleep']:
            try:
                icon_path = os.path.join(BATTLE_IMAGES_DIR, 'states', f'{state}.png')
                icon = pygame.image.load(icon_path)
                self.state_icons[state] = pygame.transform.scale(icon, (24, 24))
            except:
                print(f"Warning: Could not load {state} icon")
                surface = pygame.Surface((24, 24))
                surface.fill((255, 0, 0))
                self.state_icons[state] = surface
        
        self.level = pokemon_data.get('level', 1)
        self.experience = pokemon_data.get('experience', 0)
        self.evolution_level = pokemon_data.get('evolution_level', 0)  
        
    def draw(self, screen, position):
        self.position = position
        screen.blit(self.sprite, position)
        
    def take_damage(self, damage):
        self.current_hp = max(0, self.current_hp - damage)
        return self.current_hp <= 0
        
    def heal(self, amount):
        self.current_hp = min(self.stats['hp'], self.current_hp + amount)
        
    def is_fainted(self):
        return self.current_hp <= 0
        
    def gain_experience(self, amount):
        self.experience += amount
        # Simple level up system: need 100 exp per level
        if self.experience >= self.level * 100:
            self.level_up()
            return True
        return False
        
    def level_up(self):
        self.level += 1
        self.experience = 0
        # Increase stats on level up
        for stat in self.stats:
            self.stats[stat] = int(self.stats[stat] * 1.1)  # 10% increase
        self.current_hp = self.stats['hp']  # Heal on level up 

    def load_state_icons(self):
        self.state_icons = {}
        for state in ['poison', 'burn', 'freeze', 'asleep']:
            try:
                icon = pygame.image.load(os.path.join(BATTLE_IMAGES_DIR, 'states', f'{state}.png'))
                self.state_icons[state] = pygame.transform.scale(icon, (24, 24))
            except:
                print(f"Warning: Could not load {state} icon")
                # Create a fallback colored rectangle
                surface = pygame.Surface((24, 24))
                surface.fill((255, 0, 0))  # Red fallback
                self.state_icons[state] = surface 