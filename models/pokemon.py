import pygame
import requests
from io import BytesIO
from typing import Dict, List, Optional
from .evolution import EvolutionChain

class Move:
    def __init__(self, name: str, move_type: str, category: str, power: int, accuracy: int, pp: int):
        self.name = name
        self.type = move_type
        self.category = category  # 'physical', 'special', or 'status'
        self.power = power
        self.accuracy = accuracy
        self.pp = pp
        self.current_pp = pp
        
        # Status move effects
        self.status_effect = None  # 'paralysis', 'burn', 'freeze', 'sleep', 'poison'
        self.stat_changes = {}     # {'attack': 1, 'defense': -1} etc.
        self.effect_chance = 0     # Chance to apply status/stat changes

class Pokemon:
    def __init__(self, 
                 id: int,
                 name: str,
                 types: List[str],
                 stats: Dict[str, int],
                 sprite_url: str,
                 evolution_chain: EvolutionChain,
                 level: int = 1,
                 experience: int = 0):
        self.id = id
        self.name = name
        self.types = types
        self.stats = stats
        self.sprite_url = sprite_url
        self.evolution_chain = evolution_chain
        self.level = level
        self.experience = experience
        self.current_hp = stats["hp"]
        self.sprite = self.load_sprite()
        
        
        self.moves = self.get_default_moves()
        
        
        self.stat_stages = {
            'attack': 0, 'defense': 0, 
            'special-attack': 0, 'special-defense': 0,
            'speed': 0, 'accuracy': 0, 'evasion': 0
        }
        self.status_condition = None
        self.toxic_counter = 0

    def load_sprite(self) -> pygame.Surface:
        """Load Pokemon sprite from URL"""
        try:
            response = requests.get(self.sprite_url)
            image_data = BytesIO(response.content)
            # Load image and scale it up (Pokemon sprites are usually small)
            image = pygame.image.load(image_data)
            return pygame.transform.scale(image, (128, 128))  # Scale to 128x128 pixels
        except Exception as e:
            print(f"Error loading sprite for {self.name}: {e}")
            # Return a colored rectangle as fallback
            fallback = pygame.Surface((128, 128))
            fallback.fill((200, 200, 200))
            return fallback

    @classmethod
    def from_api_data(cls, data: Dict, evolution_chain: EvolutionChain) -> 'Pokemon':
        """Create Pokemon instance from API data"""
        return cls(
            id=data["id"],
            name=data["name"],
            types=[t["type"]["name"] for t in data["types"]],
            stats={
                "hp": data["stats"][0]["base_stat"],
                "attack": data["stats"][1]["base_stat"],
                "defense": data["stats"][2]["base_stat"],
                "special-attack": data["stats"][3]["base_stat"],
                "special-defense": data["stats"][4]["base_stat"],
                "speed": data["stats"][5]["base_stat"]
            },
            sprite_url=data["sprites"]["front_default"],
            evolution_chain=evolution_chain
        )

    @classmethod
    def from_dict(cls, data: Dict) -> 'Pokemon':
        """Create Pokemon instance from dictionary"""
        pokemon = cls(
            id=data["id"],
            name=data["name"],
            types=data["types"],
            stats=data["stats"],
            sprite_url=data["sprite_url"],
            evolution_chain=EvolutionChain.from_dict(data["evolution_chain"]),
            level=data.get("level", 1),
            experience=data.get("experience", 0)
        )
        return pokemon

    def to_dict(self) -> Dict:
        """Convert Pokemon instance to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "types": self.types,
            "stats": self.stats,
            "sprite_url": self.sprite_url,
            "evolution_chain": self.evolution_chain.to_dict(),
            "level": self.level,
            "experience": self.experience
        }

    def gain_experience(self, amount: int):
        """Add experience and level up if necessary"""
        self.experience += amount
        
        # Check for level up
        exp_needed = self.experience_to_next_level()
        while self.experience >= exp_needed:
            self.level_up()
            exp_needed = self.experience_to_next_level()

    def experience_to_next_level(self) -> int:
        return self.level * 100

    def level_up(self):
        self.level += 1
        
        # Increase stats by 10%
        for stat in self.stats:
            self.stats[stat] = int(self.stats[stat] * 1.1)
        
        self.current_hp = self.stats["hp"]

    def get_default_moves(self) -> List[Move]:
        moves = []
        # Tackle is the move used by default
        moves.append(Move('Tackle', 'normal', 'physical', 40, 100, 35))
        
        # Add type-specific move
        type_moves = {
            'fire': Move('Ember', 'fire', 'special', 40, 100, 25),
            'water': Move('Water Gun', 'water', 'special', 40, 100, 25),
            'grass': Move('Vine Whip', 'grass', 'physical', 45, 100, 25),
            'electric': Move('Thunder Shock', 'electric', 'special', 40, 100, 30),
            'normal': Move('Scratch', 'normal', 'physical', 40, 100, 35)
        }
        
        # Add a move based on the Pokemon's primary type
        primary_type = self.types[0].lower()
        if primary_type in type_moves:
            moves.append(type_moves[primary_type])
        
        # Fill remaining slots with Tackle if needed
        while len(moves) < 4:
            moves.append(Move('Tackle', 'normal', 'physical', 40, 100, 35))
        
        return moves

    