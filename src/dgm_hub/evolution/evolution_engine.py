from dgm_hub.evolution.execution_genome import ExecutionGenome
from dgm_hub.evolution.mutation_engine import MutationEngine


class EvolutionEngine:

    def __init__(self):

        self.genome=ExecutionGenome()

        self.mutator=MutationEngine()

    def learn(
        self,
        objective,
        plan,
        success,
        result
    ):

        score=1.0 if success else 0.0

        self.genome.store(

            objective,

            plan,

            success,

            score,

            result
        )

    def evolve_plan(
        self,
        plan,
        failed
    ):

        if not failed:

            return plan

        return self.mutator.mutate(
            plan
        )
