import json
import os
from config import DATA_DIR, POKEDEX_DIR
from models.pokemon import Pokemon

class DataLoader:
    def __init__(self):
        self.pokemons_data = self.load_pokemons()
        
    def load_pokemons(self):
        """Load all pokemons from pokemons.json"""
        try:
            with open(os.path.join(DATA_DIR, 'pokemons.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
            
    def get_pokemon_by_id(self, pokemon_id):
        """Get pokemon data by ID and create Pokemon instance"""
        for pokemon_data in self.pokemons_data:
            if pokemon_data['id'] == pokemon_id:
                return Pokemon(pokemon_data)
        return None
        
    def save_player_pokedex(self, player_name, pokemon_list):
        """Save player's pokemon to their personal pokedex file"""
        file_path = os.path.join(POKEDEX_DIR, f"{player_name}.json")
        pokemon_data = [{
            'id': p.id,
            'name': p.name,
            'current_hp': p.current_hp,
            'level': p.level,
            'experience': p.experience,
            'state': p.state,
            'state_duration': p.state_duration
        } for p in pokemon_list]
        with open(file_path, 'w') as f:
            json.dump(pokemon_data, f, indent=4)
            
    def load_player_pokedex(self, player_name):
        """Load player's pokemon from their personal pokedex file"""
        file_path = os.path.join(POKEDEX_DIR, f"{player_name}.json")
        try:
            with open(file_path, 'r') as f:
                pokemon_data = json.load(f)
                pokemon_list = []
                for p_data in pokemon_data:
                    pokemon = self.get_pokemon_by_id(p_data['id'])
                    if pokemon:
                        pokemon.current_hp = p_data.get('current_hp', pokemon.stats['hp']) 
                        pokemon_list.append(pokemon)
                return pokemon_list
        except FileNotFoundError:
            return None 