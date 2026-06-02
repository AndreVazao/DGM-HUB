from dgm_hub.agents.base import BaseAgent
import re


class RepairerAgent(BaseAgent):

    name = "repairer"

    def run(self, state: dict) -> dict:

        error = state.get("error", "")

        if "ModuleNotFoundError" in error:

            match = re.search(r"No module named ['\"](.+?)['\"]", error)

            module = match.group(1) if match else None

            return {
                "action": "inject_import",
                "module": module,
                "next": "tester"
            }

        return {
            "action": "manual_review_required",
            "next": "orchestrator"
        }
