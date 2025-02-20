import os
from models.game import Game
from config import PROJECT_ROOT

def check_directory_structure():
    """Create basic directory structure if it doesn't exist"""
    base_dirs = [
        'assets',
        'assets/images',
        'assets/images/menu',
        'assets/images/battle',
        'assets/images/battle/states',
        'assets/sounds',
        'assets/fonts',
        'data',
        'data/sprites',
        'data/pokedex'
    ]
    
    for directory in base_dirs:
        dir_path = os.path.join(PROJECT_ROOT, directory)
        os.makedirs(dir_path, exist_ok=True)
        print(f"Checked directory: {directory}")

def clean_pokemon_data():
    """Remove old Pokemon data to force regeneration with relative paths"""
    pokemon_json = os.path.join(PROJECT_ROOT, 'data', 'pokemons.json')
    if os.path.exists(pokemon_json):
        os.remove(pokemon_json)
        print("Removed old Pokemon data")

if __name__ == "__main__":
    check_directory_structure()
    clean_pokemon_data()
    game = Game()
    game.run() 