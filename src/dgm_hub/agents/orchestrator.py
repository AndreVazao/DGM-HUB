from dgm_hub.agents.base import BaseAgent


class OrchestratorAgent(BaseAgent):

    name = "orchestrator"

    def run(self, state: dict) -> dict:

        objective = state["objective"]

        # decisão simples (v1 deterministic routing)
        if "fix" in objective or "error" in objective:
            next_agent = "repairer"

        elif "test" in objective:
            next_agent = "tester"

        elif "build" in objective or "implement" in objective:
            next_agent = "implementer"

        else:
            next_agent = "architect"

        return {
            "next": next_agent,
            "objective": objective,
            "context": state.get("context", {})
        }
