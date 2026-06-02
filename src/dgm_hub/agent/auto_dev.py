from dataclasses import dataclass
from typing import Any


@dataclass
class DevState:
    objective: str
    last_error: str | None = None
    history: list[dict] = None
    success: bool = False

    def __post_init__(self):
        if self.history is None:
            self.history = []


class AutoDevAgent:

    def __init__(self, runtime):
        self.runtime = runtime

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    def run(self, objective: str, max_steps: int = 8):

        state = DevState(objective=objective)

        for step in range(max_steps):

            action = self.plan(state)

            result = self.execute(action)

            state.history.append({
                "step": step,
                "action": action,
                "result": self._safe_result(result)
            })

            # erro detetado
            if self._is_error(result):
                state.last_error = self._extract_error(result)
                continue

            # sucesso
            if self._is_success(result):
                state.success = True
                break

            # feed loop (aprende com output)
            state.last_error = None

        return state

    # -----------------------------
    # DECISION ENGINE (MVP INTEL)
    # -----------------------------
    def plan(self, state: DevState):

        obj = state.objective.lower()
        err = (state.last_error or "").lower()

        # prioridade: corrigir erro
        if state.last_error:

            if "module not found" in err:
                return {
                    "tool": "git",
                    "args": {
                        "operation": "status",
                        "repo_path": "C:\\ProgramasGodMode\\DGM-HUB"
                    }
                }

            if "permission" in err:
                return {
                    "tool": "filesystem",
                    "args": {
                        "operation": "read",
                        "path": "C:\\AI\\test.txt"
                    }
                }

        # default behaviours
        if "git" in obj:
            return {
                "tool": "git",
                "args": {
                    "operation": "status",
                    "repo_path": "C:\\ProgramasGodMode\\DGM-HUB"
                }
            }

        if "tree" in obj or "repo" in obj:
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

    # -----------------------------
    # EXECUTION
    # -----------------------------
    def execute(self, action: dict):

        tool = self.runtime.registry.get(action["tool"])

        return tool.execute(**action["args"])

    # -----------------------------
    # RESULT PARSING
    # -----------------------------
    def _is_error(self, result: Any) -> bool:
        if isinstance(result, dict):
            return "error" in result or "traceback" in result
        return False

    def _extract_error(self, result: Any) -> str:
        if isinstance(result, dict):
            return str(result.get("error") or result.get("traceback"))
        return str(result)

    def _is_success(self, result: Any) -> bool:
        if isinstance(result, dict):
            return result.get("status") in ["ok", "success", "committed"]
        return False

    def _safe_result(self, result: Any):
        try:
            return str(result)[:500]
        except:
            return "unserializable"
