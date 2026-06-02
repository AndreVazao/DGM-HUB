from dgm_hub.agents.base import BaseAgent


class ImplementerAgent(BaseAgent):

    name = "implementer"

    def run(self, state: dict) -> dict:

        git = self.runtime.registry.get("git")

        result = git.execute(
            operation="status",
            repo_path="C:\\ProgramasGodMode\\DGM-HUB"
        )

        return {
            "changes_detected": result,
            "next": "tester",
            "context": state
        }
