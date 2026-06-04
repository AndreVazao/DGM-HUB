from dataclasses import dataclass, field
import uuid
import time
from typing import Dict, Any


@dataclass
class PatchGenome:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patch: str = ""
    error_signature: str = ""

    created_at: float = field(default_factory=time.time)

    parent_id: str | None = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    fitness: float = 0.0
    survival_score: float = 0.0
    reuse_score: float = 0.0

    def score(self):
        """
        Combined evolutionary score.
        """
        return (
            self.fitness * 0.5 +
            self.survival_score * 0.3 +
            self.reuse_score * 0.2
        )
