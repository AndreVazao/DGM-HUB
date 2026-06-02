from typing import Any
from dgm_hub.agent.self_rewriting_engine import SelfRewritingEngine


class AgentEngine:

    def __init__(self, runtime):
        self.runtime = runtime
        self.rewriter = SelfRewritingEngine(runtime, self)

    def run(self, objective: str):
        """
        v3 execution entry: delegates to rewriter
        """
        return self.rewriter.run(objective)

    # -----------------------------
    # PLANNER (Required by Rewriter)
    # -----------------------------
    def plan(self, objective: str) -> dict:
        """
        Simple heuristic planner for the execution loop
        """
        text = objective.lower()

        if "git" in text:
            return {
                "tool": "git",
                "args": {"operation": "status"}
            }

        if "files" in text or "tree" in text:
            return {
                "tool": "repo",
                "args": {"operation": "tree"}
            }

        return {
            "tool": "cmd",
            "args": {"command": f"echo execution objective: {objective}"}
        }
