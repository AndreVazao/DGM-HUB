class DebateEngine:

    def resolve(self, proposals):

        resolved = []

        for role, items in proposals.items():

            for item in items:

                if item is None or item.get("proposal") is None:
                    continue

                # normalização de ideias
                score = self._score(item)

                resolved.append({
                    "role": role,
                    "proposal": item["proposal"],
                    "score": score
                })

        return resolved

    def _score(self, proposal):

        score = 0
        p_str = str(proposal).lower()

        if "performance" in p_str:
            score += 2

        if "refactor" in p_str:
            score += 1

        if "security" in p_str:
            score += 3

        if "architect" in p_str:
            score += 1

        return score
