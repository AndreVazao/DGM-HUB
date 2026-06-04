from typing import List
import random
from dgm_hub.evolution.strategy_genome import StrategyGenome


class AgentEvolver:

    def __init__(self):
        self.population: List[StrategyGenome] = []

    def seed(self, base_agents: List[StrategyGenome]):
        self.population.extend(base_agents)

    def select_best(self, top_k=3):
        return sorted(
            self.population,
            key=lambda a: a.fitness,
            reverse=True
        )[:top_k]

    def reproduce(self):
        """
        Create new agents from best performers.
        """
        parents = self.select_best()

        children = []

        for p in parents:
            child = StrategyGenome(
                name=p.name + "_mutant",
                parent_id=p.id,
                heuristics=p.heuristics.copy()
            ).mutate()

            children.append(child)

        self.population.extend(children)
        return children
