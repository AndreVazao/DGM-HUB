class BaseAgent:

    name = "base"

    def __init__(self, runtime):
        self.runtime = runtime

    def run(self, state: dict) -> dict:
        raise NotImplementedError
