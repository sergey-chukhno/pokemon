import json
import os
from typing import Dict, Optional

class FileHandler:
    def __init__(self):
        self.data_dir = "data"
        self.pokemons_file = os.path.join(self.data_dir, "pokemons.json")
        self.pokedex_dir = os.path.join(self.data_dir, "pokedex")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.pokedex_dir, exist_ok=True)

    def save_pokemons(self, data: Dict):
        """Save Pokemon data to JSON file"""
        with open(self.pokemons_file, 'w') as f:
            json.dump(data, f, indent=4)

    def load_pokemons(self) -> Optional[Dict]:
        """Load Pokemon data from JSON file"""
        if os.path.exists(self.pokemons_file):
            with open(self.pokemons_file, 'r') as f:
                return json.load(f)
        return None

    def save_pokedex(self, player_name: str, data: Dict):
        """Save player's Pokedex to JSON file"""
        file_path = os.path.join(self.pokedex_dir, f"{player_name}.json")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def load_pokedex(self, player_name: str) -> Optional[Dict]:
        """Load player's Pokedex from JSON file"""
        file_path = os.path.join(self.pokedex_dir, f"{player_name}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None 