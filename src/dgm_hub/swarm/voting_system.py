import random

class VotingSystem:
    """
    Select best patch from competing agents.
    """

    def select_best(self, patches: list[dict]) -> dict:

        # weighted confidence + randomness (exploration)
        scored = []

        for p in patches:
            score = p.get("confidence", 0.5)

            # slight stochastic exploration
            score += random.uniform(-0.05, 0.05)

            scored.append((score, p))

        scored.sort(reverse=True, key=lambda x: x[0])

        return {
            "patch": scored[0][1]["patch"],
            "winner": scored[0][1]["agent"],
            "all": patches
        }
