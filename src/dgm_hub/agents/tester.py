from dgm_hub.agents.base import BaseAgent
import subprocess


class TesterAgent(BaseAgent):

    name = "tester"

    def run(self, state: dict) -> dict:

        result = subprocess.run(
            ["python", "-m", "pytest", "-q"],
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "next": "repairer" if result.returncode != 0 else "orchestrator"
        }
