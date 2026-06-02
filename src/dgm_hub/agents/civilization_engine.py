from dgm_hub.agents.orchestrator import OrchestratorAgent
from dgm_hub.agents.architect import ArchitectAgent
from dgm_hub.agents.implementer import ImplementerAgent
from dgm_hub.agents.tester import TesterAgent
from dgm_hub.agents.repairer import RepairerAgent


class CivilizationEngine:

    def __init__(self, runtime):

        self.runtime = runtime

        self.agents = {
            "orchestrator": OrchestratorAgent(runtime),
            "architect": ArchitectAgent(runtime),
            "implementer": ImplementerAgent(runtime),
            "tester": TesterAgent(runtime),
            "repairer": RepairerAgent(runtime),
        }

    def run(self, objective: str, max_cycles: int = 10):

        state = {"objective": objective}

        current = "orchestrator"

        for i in range(max_cycles):

            agent = self.agents[current]

            print(f"[CIV] cycle {i} -> {current}")

            result = agent.run(state)

            state.update(result)

            current = result.get("next", "orchestrator")

        return state
