from typing import List
from dgm_hub.evolution.strategy_genome import StrategyGenome


class SelectionPressure:

    def apply(self, population: List[StrategyGenome]) -> List[StrategyGenome]:
        """
        Remove weak agents.
        """

        if not population:
            return []

        avg_fitness = sum(p.fitness for p in population) / len(population)

        survivors = [
            p for p in population
            if p.fitness >= avg_fitness * 0.75
        ]

        return survivors
