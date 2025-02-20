import pygame
import json
import os
from pygame.locals import *
from pokemon import Pokemon
from battle import Battle

pygame.init()

# Fenêtre
width = 800
height = 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pokemon")
pygame.font.init()
font = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 25)
font_poke = pygame.font.Font('poke_font.ttf', 20)
font_poke_small = pygame.font.Font('poke_font.ttf', 15)

# Couleurs
black = (0, 0, 0)
white = (255, 255, 255)
grey = (200, 200, 200)
green = (0, 200, 0)
red = (200, 0, 0)

# Chargement des images
background = pygame.image.load('images/background.png')
background = pygame.transform.scale(background, (800, 500))
button_bar = pygame.image.load('images/button_bar.png')
button_bar = pygame.transform.scale(button_bar, (400, 100))
fight_button = pygame.image.load('images/fight_button.png')
bag_button = pygame.image.load('images/bag_button.png')
pokemon_button = pygame.image.load('images/pokemon_button.png')
run_button = pygame.image.load('images/run_button.png')
attackbox = pygame.image.load('images/attackbox.png')
attackbox = pygame.transform.scale(attackbox, (800, 100))
pokedex = pygame.image.load('images/pokedex.png')
pokedex = pygame.transform.scale(pokedex, (800, 600))
podex_box = pygame.image.load('images/pokedex_box.png')
podex_box = pygame.transform.scale(podex_box, (250, 100))
background_poke = pygame.image.load('images/background_poke.png')
background_poke = pygame.transform.scale(background_poke, (800, 600))

images = {
    'background': background,
    'button_bar': button_bar,
    'fight_button': fight_button,
    'bag_button': bag_button,
    'pokemon_button': pokemon_button,
    'run_button': run_button,
    'attackbox': attackbox,
    'pokedex': pokedex,
    'podex_box': podex_box,
    'background_poke': background_poke
}
fonts = {
    'font': font,
    'font_s': font_small,
    'font_poke': font_poke,
    'font_poke_s': font_poke_small
}
colors = {
    'black': black,
    'white': white,
    'grey': grey,
    'green': green,
    'red': red
}

# Création des Pokémon pour la sélection
level = 5
bulbasaur = Pokemon('Bulbasaur', level, 150, 250)
charmander = Pokemon('Charmander', level, 350, 250)
squirtle = Pokemon('Squirtle', level, 550, 250)
pokemons = [bulbasaur, charmander, squirtle]

# Variables de jeu
selection_menu = False
main_menu = True
battle = None
running = True
hovered_attack = None

file_path = "player_pokemon.json"

def load_player_pokemon():
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            try:
                data = json.load(file)
                pokemons = []
                for p in data:
                    pokemon = Pokemon(p['name'], p['level'], 150, 250)
                    pokemon.current_hp = p['current_hp']
                    pokemon.max_hp = p['max_hp']
                    pokemon.types = p['types']
                    pokemon.attacks = [{'move': {'name': attack}} for attack in p['attacks']]
                    pokemons.append(pokemon)
                return pokemons
            except json.JSONDecodeError:
                return []
    return []

def save_player_pokemon(pokemon_list):
    data = [{
        "name": p.name,
        "level": p.level,
        "current_hp": p.current_hp,
        "max_hp": p.max_hp,
        "types": p.types,
        "attacks": [move["move"]["name"] for move in p.attacks]
    } for p in pokemon_list]

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def draw_main_menu():
    screen.fill(white)
    title = font.render("Pokemon Game", True, black)
    title_rect = title.get_rect(center=(width/2, 100))
    screen.blit(title, title_rect)

    new_game_button = pygame.Rect(width/2 - 100, 200, 200, 50)
    load_game_button = pygame.Rect(width/2 - 100, 300, 200, 50)
    quit_button = pygame.Rect(width/2 - 100, 400, 200, 50)

    pygame.draw.rect(screen, green, new_game_button)
    pygame.draw.rect(screen, green, load_game_button)
    pygame.draw.rect(screen, red, quit_button)

    new_game_text = font.render("New Game", True, white)
    load_game_text = font.render("Load Game", True, white)
    quit_text = font.render("Quit", True, white)

    screen.blit(new_game_text, (new_game_button.x + 50, new_game_button.y + 15))
    screen.blit(load_game_text, (load_game_button.x + 50, load_game_button.y + 15))
    screen.blit(quit_text, (quit_button.x + 80, quit_button.y + 15))

    return new_game_button, load_game_button, quit_button

player_pokemons = load_player_pokemon()

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        if event.type == MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if main_menu:
                new_game_button, load_game_button, quit_button = draw_main_menu()
                if new_game_button.collidepoint(mouse_pos):
                    main_menu = False
                    selection_menu = True
                    player_pokemons = []
                    save_player_pokemon(player_pokemons)
                elif load_game_button.collidepoint(mouse_pos):
                    main_menu = False
                    selection_menu = False
                    player_pokemons = load_player_pokemon()
                    if player_pokemons:
                        selected_pokemon = player_pokemons[0]
                        battle = Battle(selected_pokemon, screen, fonts, images, colors)
                    else:
                        main_menu = True
                elif quit_button.collidepoint(mouse_pos):
                    running = False

            # Sélection du Pokémon au début
            if event.type == MOUSEBUTTONDOWN and selection_menu:
                mouse_pos = pygame.mouse.get_pos()
                for pkmn in pokemons:
                    if pkmn.click(mouse_pos):
                        selected_pokemon = pkmn
                        selection_menu = False
                        player_pokemons.append(selected_pokemon)
                        save_player_pokemon(player_pokemons)
                        battle = Battle(selected_pokemon, screen, fonts, images, colors)

            # Gestion des clics en mode combat ou Pokédex
            if event.type == MOUSEBUTTONDOWN and not selection_menu and not main_menu:
                mouse_pos = pygame.mouse.get_pos()
                if battle.pokedex_show:
                    battle.handle_pokedex_click(mouse_pos)
                else:
                    if battle.fight_button_rect.collidepoint(mouse_pos):
                        battle.show_attacks = True
                        battle.attacks_buttons()
                    elif battle.show_attacks and battle.current_turn == 'player':
                        for btn in battle.attack_buttons:
                            if btn.rect.collidepoint(mouse_pos):
                                battle.handle_attack(btn.text)
                                battle.show_attacks = False
                    elif battle.pokemon_button_rect.collidepoint(mouse_pos):
                        battle.pokedex_show = True

        # Gestion du survol pour afficher les infos d'une attaque
        if event.type == MOUSEMOTION and battle and battle.show_attacks:
            mouse_pos = pygame.mouse.get_pos()
            hovered_attack = None
            for btn in battle.attack_buttons:
                if btn.rect.collidepoint(mouse_pos):
                    hovered_attack = btn.text
                    break

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE and battle and battle.pokedex_show:
                battle.pokedex_show = False

    # Affichage de l'écran selon le mode
    if main_menu:
        draw_main_menu()
    elif selection_menu:
        screen.fill(white)
        title = font.render("Choose your Pokemon!", True, black)
        title_rect = title.get_rect(center=(width/2, 50))
        screen.blit(title, title_rect)

        # Affichage des sprites des Pokémon
        bulbasaur.draw(screen)
        charmander.draw(screen)
        squirtle.draw(screen)
    else:
        battle.draw(hovered_attack)

    pygame.display.update()