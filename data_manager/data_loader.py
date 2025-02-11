from typing import Dict, List
from .api_handler import PokeAPIHandler
from .file_handler import FileHandler
from models.pokemon import Pokemon
from models.evolution import EvolutionChain

class DataLoader:
    def __init__(self):
        self.api_handler = PokeAPIHandler()
        self.file_handler = FileHandler()

    def initialize_pokemon_data(self, num_pokemon: int = 25) -> Dict[str, Pokemon]:
        """Initialize or load Pokemon data"""
        existing_data = self.file_handler.load_pokemons()
        
        if existing_data:
            return {name: Pokemon.from_dict(data) for name, data in existing_data.items()}
        
        pokemons = {}
        for i in range(1, num_pokemon + 1):
            # Fetch Pokemon data
            pokemon_data = self.api_handler.fetch_pokemon(i)
            species_data = self.api_handler.fetch_species_data(i)
            
            # Create evolution chain
            evolution_data = self.api_handler.fetch_evolution_chain(
                species_data["evolution_chain"]["url"]
            )
            evolution_chain = EvolutionChain.from_api_data(evolution_data)
            
            # Create Pokemon instance
            pokemon = Pokemon.from_api_data(pokemon_data, evolution_chain)
            pokemons[pokemon.name] = pokemon

        # Save to file
        self.file_handler.save_pokemons({
            name: pokemon.to_dict() for name, pokemon in pokemons.items()
        })
        
        return pokemons 