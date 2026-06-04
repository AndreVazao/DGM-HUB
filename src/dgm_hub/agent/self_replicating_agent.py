from dgm_hub.evolution.strategy_genome import StrategyGenome
import copy


class SelfReplicatingAgent:

    def __init__(self, genome: StrategyGenome):
        self.genome = genome

    def think(self, context: dict):
        """
        Decide strategy based on genome.
        """

        if self.genome.exploration_bias > 0.7:
            return "explore"

        if self.genome.risk_tolerance > 0.6:
            return "aggressive_patch"

        return "safe_patch"

    def replicate(self):
        """
        Create mutated version of self.
        """
        new_genome = copy.deepcopy(self.genome).mutate()
        new_genome.parent_id = self.genome.id
        return SelfReplicatingAgent(new_genome)
