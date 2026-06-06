from typing import Dict, Any
from dgm_hub.evolution.genome import PatchGenome


class FitnessEngine:
    """
    Evaluates how good a patch is based on real execution.
    """

    def evaluate(self, genome: PatchGenome, test_result: Any) -> PatchGenome:
        if test_result is None:
             genome.fitness = 0.0
             genome.survival_score = 0.0
             genome.reuse_score = 0.0
             return genome

        if isinstance(test_result, dict):
            genome.fitness = 1.0 if test_result.get("passed") else 0.0
            genome.survival_score = 1.0 - test_result.get("crash_rate", 0.0)
            genome.reuse_score = test_result.get("historical_similarity", 0.0)
        else:
            # Handle TestResult dataclass
            passed = getattr(test_result, "passed", False)
            genome.fitness = 1.0 if passed else 0.0
            genome.survival_score = 1.0 - getattr(test_result, "crash_rate", 0.0)
            genome.reuse_score = getattr(test_result, "historical_similarity", 0.0)

        return genome
