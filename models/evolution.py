from typing import Dict, List, Optional

class EvolutionStage:
    def __init__(self, name: str, min_level: int):
        self.name = name
        self.min_level = min_level

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "min_level": self.min_level
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EvolutionStage':
        return cls(
            name=data["name"],
            min_level=data["min_level"]
        )

class EvolutionChain:
    def __init__(self, stages: List[EvolutionStage]):
        self.stages = stages

    def get_next_evolution(self, current_name: str) -> Optional[EvolutionStage]:
        """Get next evolution stage for given Pokemon name"""
        for i, stage in enumerate(self.stages[:-1]):
            if stage.name == current_name:
                return self.stages[i + 1]
        return None

    def to_dict(self) -> Dict:
        return {
            "stages": [stage.to_dict() for stage in self.stages]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EvolutionChain':
        return cls(
            stages=[EvolutionStage.from_dict(stage_data) 
                   for stage_data in data["stages"]]
        )

    @classmethod
    def from_api_data(cls, data: Dict) -> 'EvolutionChain':
        """Create EvolutionChain from API response"""
        stages = []
        current = data["chain"]
        min_level = 1
        
        while current:
            stages.append(EvolutionStage(
                name=current["species"]["name"],
                min_level=min_level
            ))
            
            if not current["evolves_to"]:
                break
                
            current = current["evolves_to"][0]
            # Get evolution details (simplified)
            min_level += 16  # Simplified evolution level requirement
            
        return cls(stages=stages) 