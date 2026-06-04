from typing import Dict
from dgm_hub.evolution.genome import PatchGenome


class FitnessEngine:
    """
    Evaluates how good a patch is based on real execution.
    """

    def evaluate(self, genome: PatchGenome, test_result: Dict) -> PatchGenome:

        genome.fitness = 1.0 if test_result.get("passed") else 0.0

        # survival = system stability after patch
        genome.survival_score = 1.0 - test_result.get("crash_rate", 0.0)

        # reuse score = if similar past patches succeeded
        genome.reuse_score = test_result.get("historical_similarity", 0.0)

        return genome
