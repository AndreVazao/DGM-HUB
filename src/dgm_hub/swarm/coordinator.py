from typing import List, Dict


class BasicSwarmCoordinator:
    """
    Splits tasks into sub-workers and merges results
    """

    def __init__(self, runtime):
        self.runtime = runtime

    def dispatch(self, objective: str) -> List[Dict]:

        # simple decomposition logic (v1)
        return [
            {"role": "planner", "objective": objective},
            {"role": "executor", "objective": objective},
            {"role": "verifier", "objective": objective}
        ]

    def merge(self, results: List[dict]) -> dict:

        return {
            "status": "merged",
            "results": results
        }
