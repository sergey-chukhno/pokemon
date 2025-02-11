import requests
from typing import Dict, List

class PokeAPIHandler:
    BASE_URL = "https://pokeapi.co/api/v2"

    @staticmethod
    def fetch_pokemon(pokemon_id: int) -> Dict:
        """Fetch basic Pokemon data from PokeAPI"""
        response = requests.get(f"{PokeAPIHandler.BASE_URL}/pokemon/{pokemon_id}")
        return response.json()

    @staticmethod
    def fetch_species_data(pokemon_id: int) -> Dict:
        """Fetch Pokemon species data from PokeAPI"""
        response = requests.get(f"{PokeAPIHandler.BASE_URL}/pokemon-species/{pokemon_id}")
        return response.json()

    @staticmethod
    def fetch_evolution_chain(chain_url: str) -> Dict:
        """Fetch evolution chain data from PokeAPI"""
        response = requests.get(chain_url)
        return response.json() 