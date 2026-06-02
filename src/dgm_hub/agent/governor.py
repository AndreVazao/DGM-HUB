from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class GovernanceDecision:
    allowed: bool
    reason: str
    modified_objective: str | None = None
    flags: Dict[str, Any] = None


class CognitiveGovernor:
    """
    Civilisation Core Gatekeeper
    - controla execução
    - limita loops
    - aplica policy
    """

    def __init__(self, policy: dict):
        self.policy = policy
        self.recent_objectives = []

    def evaluate(self, objective: str) -> GovernanceDecision:

        self.recent_objectives.append(objective)

        # -------------------------
        # LOOP DETECTION
        # -------------------------
        if self.recent_objectives.count(objective) > 3:
            return GovernanceDecision(
                allowed=False,
                reason="loop_detected",
                flags={"type": "repetition_limit"}
            )

        # -------------------------
        # BLOCK DANGEROUS OPS
        # -------------------------
        blocked_keywords = self.policy.get("blocked_keywords", [])
        for k in blocked_keywords:
            if k in objective.lower():
                return GovernanceDecision(
                    allowed=False,
                    reason=f"blocked_keyword:{k}"
                )

        # -------------------------
        # DEFAULT ALLOW
        # -------------------------
        return GovernanceDecision(
            allowed=True,
            reason="approved"
        )
