import pygame
import sys
from data_manager.data_loader import DataLoader
from menu import MenuSystem
from battle import BattleSystem

class PokemonGame:
    def __init__(self):
        pygame.init()
        
        # Constants
        self.WINDOW_WIDTH = 800
        self.WINDOW_HEIGHT = 600
        self.FPS = 60
        
        # Set up display
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Pokemon Game")
        self.clock = pygame.time.Clock()
        
        # Initialize systems
        self.data_loader = DataLoader()
        self.pokemons = self.data_loader.initialize_pokemon_data()
        self.menu = MenuSystem(self.screen, self.pokemons)
        self.battle = BattleSystem(self.screen, self.pokemons)
        
    
        self.current_player = None
        self.running = True

    def run(self):
        self.running = True
        battle_return_data = None
        
        while self.running:
            result = self.menu.show_main_menu()
            
            if result is None:
                self.running = False
            elif result["action"] == "quit":
                self.running = False
            elif result["action"] == "battle":
                while True:  # Battle-Pokedex loop
                    battle_result = self.battle.start(result["player_data"])
                    
                    if battle_result["action"] == "quit":
                        self.running = False
                        break
                    elif battle_result["action"] == "return_to_menu":
                        break
                    elif battle_result["action"] == "open_pokedex":
                        # Open Pokedex and wait for Pokemon selection
                        pokedex_result = self.menu.show_pokedex_menu(result["player_data"])
                        
                        if pokedex_result["action"] == "quit":
                            self.running = False
                            break
                        elif pokedex_result["action"] == "pokemon_selected":
                            # Update player's Pokemon and continue battle
                            result["player_data"]["pokemons"][0] = pokedex_result["selected_pokemon"]
                            continue
                        else:
                            break

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = PokemonGame()
    game.run()
