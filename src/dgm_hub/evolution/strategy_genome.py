from dataclasses import dataclass, field
import uuid
from typing import Dict, Any


@dataclass
class StrategyGenome:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    name: str = ""
    description: str = ""

    mutation_rate: float = 0.1
    exploration_bias: float = 0.5
    risk_tolerance: float = 0.5

    heuristics: Dict[str, Any] = field(default_factory=dict)

    fitness: float = 0.0

    parent_id: str | None = None

    def mutate(self):
        """
        Small stochastic evolution step.
        """
        import random

        if random.random() < self.mutation_rate:
            self.exploration_bias += random.uniform(-0.05, 0.05)
            self.risk_tolerance += random.uniform(-0.05, 0.05)

        self.exploration_bias = max(0.0, min(1.0, self.exploration_bias))
        self.risk_tolerance = max(0.0, min(1.0, self.risk_tolerance))

        return self
