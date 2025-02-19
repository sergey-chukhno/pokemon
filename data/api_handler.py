import requests
import json
import os
from config import POKEAPI_BASE_URL, DATA_DIR

def fetch_pokemon_data(pokemon_id):
    """Fetch Pokemon data from PokeAPI"""
    url = f"{POKEAPI_BASE_URL}/pokemon/{pokemon_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def fetch_pokemon_species(pokemon_id):
    """Fetch Pokemon species data for evolution info"""
    url = f"{POKEAPI_BASE_URL}/pokemon-species/{pokemon_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def download_pokemon_sprite(pokemon_id):
    """Download Pokemon sprite and save it"""
    pokemon_data = fetch_pokemon_data(pokemon_id)
    if pokemon_data:
        sprite_url = pokemon_data['sprites']['front_default']
        response = requests.get(sprite_url)
        if response.status_code == 200:
            sprite_path = os.path.join(DATA_DIR, 'sprites', f'{pokemon_id}.png')
            os.makedirs(os.path.dirname(sprite_path), exist_ok=True)
            with open(sprite_path, 'wb') as f:
                f.write(response.content)
            return sprite_path
    return None

def initialize_pokemon_database(count=30):
    """Initialize the Pokemon database with the first 'count' Pokemon"""
    pokemon_list = []
    for i in range(1, count + 1):
        pokemon_data = fetch_pokemon_data(i)
        species_data = fetch_pokemon_species(i)
        if pokemon_data and species_data:
            # Get evolution level from species data
            evolution_level = 0
            if species_data.get('evolves_to'):
                evolution_details = species_data['evolves_to'][0].get('evolution_details', [{}])[0]
                if evolution_details.get('min_level'):
                    evolution_level = evolution_details['min_level']
                else:
                    evolution_level = 16  # Default evolution level if not specified
            
            pokemon = {
                'id': pokemon_data['id'],
                'name': pokemon_data['name'],
                'types': [t['type']['name'] for t in pokemon_data['types']],
                'stats': {
                    'hp': pokemon_data['stats'][0]['base_stat'],
                    'attack': pokemon_data['stats'][1]['base_stat'],
                    'defense': pokemon_data['stats'][2]['base_stat'],
                    'speed': pokemon_data['stats'][5]['base_stat']
                },
                'moves': [move['move']['name'] for move in pokemon_data['moves'][:4]],
                'sprite_path': download_pokemon_sprite(i),
                'evolution_level': evolution_level
            }
            pokemon_list.append(pokemon)
    
    # Save to pokemons.json
    with open(os.path.join(DATA_DIR, 'pokemons.json'), 'w') as f:
        json.dump(pokemon_list, f, indent=4) 