class SwarmLoop:

    def __init__(self, coordinator):
        self.coordinator = coordinator

    def run(self, task: str):

        result = self.coordinator.execute_task(task)

        winner = result["winner"]

        if winner and winner["proposal"]:

            return {
                "status": "accepted",
                "execution": winner
            }

        return {
            "status": "no_consensus"
        }
