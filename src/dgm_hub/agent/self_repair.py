from dataclasses import dataclass
from typing import Any
import traceback


@dataclass
class RepairState:
    objective: str
    success: bool = False
    last_error: str | None = None
    history: list[dict] = None
    fixes_applied: int = 0

    def __post_init__(self):
        if self.history is None:
            self.history = []


class SelfRepairEngine:

    def __init__(self, runtime):
        self.runtime = runtime
        self.repo_path = "C:\\ProgramasGodMode\\DGM-HUB"

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    def run(self, objective: str, max_cycles: int = 5):

        state = RepairState(objective=objective)

        for cycle in range(max_cycles):

            try:
                result = self._execute(objective)

                state.history.append({
                    "cycle": cycle,
                    "result": self._safe(result)
                })

                if self._is_success(result):
                    state.success = True
                    break

            except Exception as e:

                error = traceback.format_exc()
                state.last_error = error

                fix_action = self._decide_fix(error)

                fix_result = self._apply_fix(fix_action)

                state.fixes_applied += 1

                state.history.append({
                    "cycle": cycle,
                    "error": error,
                    "fix": fix_action,
                    "fix_result": self._safe(fix_result)
                })

        return state

    # -----------------------------
    # EXECUTION
    # -----------------------------
    def _execute(self, objective: str):

        if "git" in objective.lower():

            return self.runtime.registry.get("git").execute(
                operation="status",
                repo_path=self.repo_path
            )

        if "repo" in objective.lower():

            return self.runtime.registry.get("repo").execute(
                operation="tree",
                repo_path=self.repo_path
            )

        return {"status": "unknown objective"}

    # -----------------------------
    # ERROR ANALYSIS + FIX STRATEGY
    # -----------------------------
    def _decide_fix(self, error: str):

        err = error.lower()

        # missing module / import issues
        if "modulenotfounderror" in err:
            return {
                "type": "git_status_check"
            }

        # path issues
        if "permission" in err:
            return {
                "type": "filesystem_check",
                "path": "C:\\AI"
            }

        # default fallback
        return {
            "type": "git_status_check"
        }

    # -----------------------------
    # APPLY FIXES (REAL TOOLS)
    # -----------------------------
    def _apply_fix(self, fix: dict):

        t = fix.get("type")

        if t == "git_status_check":

            return self.runtime.registry.get("git").execute(
                operation="status",
                repo_path=self.repo_path
            )

        if t == "filesystem_check":

            return self.runtime.registry.get("filesystem").execute(
                operation="read",
                path=fix["path"]
            )

        return {"status": "no_fix_applied"}

    # -----------------------------
    # SUCCESS DETECTION
    # -----------------------------
    def _is_success(self, result: Any) -> bool:

        if isinstance(result, dict):
            return "error" not in result and "traceback" not in result

        return True

    def _safe(self, result: Any):

        try:
            return str(result)[:500]
        except:
            return "unserializable"
