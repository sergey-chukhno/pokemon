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

# Paths
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(GAME_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
MENU_IMAGES_DIR = os.path.join(IMAGES_DIR, "menu")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
DATA_DIR = os.path.join(GAME_DIR, "data")
POKEDEX_DIR = os.path.join(DATA_DIR, "pokedex")

# Add battle backgrounds path
BATTLE_IMAGES_DIR = os.path.join(IMAGES_DIR, "battle")
BATTLE_ATTACKS_DIR = os.path.join(BATTLE_IMAGES_DIR, "animation")

# Create directories if they don't exist
os.makedirs(POKEDEX_DIR, exist_ok=True)

# API
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

# Game settings
INITIAL_POKEMON_COUNT = 30
MAX_PLAYER_POKEMON = 3 