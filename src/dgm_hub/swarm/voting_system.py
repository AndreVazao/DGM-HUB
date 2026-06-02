class VotingSystem:

    def select_best(self, proposals):

        if not proposals:
            return None

        sorted_items = sorted(
            proposals,
            key=lambda x: x["score"],
            reverse=True
        )

        return sorted_items[0]
