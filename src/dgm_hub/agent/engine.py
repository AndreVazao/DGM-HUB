from dataclasses import dataclass
from typing import Any


@dataclass
class AgentState:
    objective: str
    history: list[dict]
    finished: bool = False


class AgentEngine:

    def __init__(self, runtime):
        self.runtime = runtime

    def run(self, objective: str, max_steps: int = 10):

        state = AgentState(
            objective=objective,
            history=[]
        )

        for _ in range(max_steps):

            action = self.decide_next_action(state)

            result = self.execute(action)

            state.history.append({
                "action": action,
                "result": result
            })

            if self.is_done(result, state):
                state.finished = True
                break

        return state

    # -------------------------
    # CORE DECISION LOGIC
    # -------------------------
    def decide_next_action(self, state: AgentState):

        # MVP brain (sem LLM ainda)
        if "git" in state.objective.lower():
            return {
                "tool": "git",
                "args": {
                    "operation": "status",
                    "repo_path": "C:\\ProgramasGodMode\\DGM-HUB"
                }
            }

        if "files" in state.objective.lower():
            return {
                "tool": "repo",
                "args": {
                    "operation": "tree",
                    "repo_path": "C:\\ProgramasGodMode\\DGM-HUB"
                }
            }

        return {
            "tool": "git",
            "args": {
                "operation": "status",
                "repo_path": "C:\\ProgramasGodMode\\DGM-HUB"
            }
        }

    def execute(self, action: dict):
        return self.runtime.registry.get(
            action["tool"]
        ).execute(**action["args"])

    def is_done(self, result: Any, state: AgentState):
        return False
