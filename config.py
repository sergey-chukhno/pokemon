import pygame
import os

# Window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BRIGHT_YELLOW = (255, 255, 0)
BUTTON_BLACK = (0, 0, 0, 180)  

# Get the project root directory (where main.py is)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
MENU_IMAGES_DIR = os.path.join(IMAGES_DIR, "menu")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
POKEDEX_DIR = os.path.join(DATA_DIR, "pokedex")

# Battle paths
BATTLE_IMAGES_DIR = os.path.join(IMAGES_DIR, "battle")
BATTLE_ATTACKS_DIR = os.path.join(BATTLE_IMAGES_DIR, "animation")

# Required directory structure
REQUIRED_DIRS = [
    os.path.join(DATA_DIR, 'sprites'),
    os.path.join(DATA_DIR, 'pokedex'),
    os.path.join(IMAGES_DIR, 'battle', 'states'),
    os.path.join(IMAGES_DIR, 'battle', 'sounds'),
    os.path.join(IMAGES_DIR, 'battle', 'animation'),
    os.path.join(SOUNDS_DIR, 'menu'),
    os.path.join(SOUNDS_DIR, 'battle'),
    os.path.join(SOUNDS_DIR, 'attacks'),
]

# Create all required directories
for directory in REQUIRED_DIRS:
    os.makedirs(directory, exist_ok=True)

# API
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

# Game settings
INITIAL_POKEMON_COUNT = 30
MAX_PLAYER_POKEMON = 3 