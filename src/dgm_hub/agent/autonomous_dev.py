from dataclasses import dataclass
from typing import Any
from pathlib import Path
import traceback
import os


@dataclass
class DevState:
    objective: str
    success: bool = False
    last_error: str | None = None
    fixes: int = 0
    history: list[dict] = None

    def __post_init__(self):
        if self.history is None:
            self.history = []


class AutonomousDevEngine:

    def __init__(self, runtime, repo_path: str | Path | None = None):
        self.runtime = runtime
        if repo_path:
            self.repo_path = Path(repo_path).resolve()
        else:
            env_path = os.environ.get("DGM_REPO_PATH")
            self.repo_path = Path(env_path).resolve() if env_path else Path(".").resolve()

    def run(self, objective: str, max_cycles: int = 5):
        state = DevState(objective=objective)
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
            except Exception:
                error = traceback.format_exc()
                state.last_error = error
                fix = self._analyze_and_fix(error)
                fix_result = self._apply_fix(fix)
                state.fixes += 1
                state.history.append({
                    "cycle": cycle,
                    "error": error,
                    "fix": fix,
                    "fix_result": self._safe(fix_result)
                })
        if state.success:
            self._commit_changes()
        return state

    def _execute(self, objective: str):
        obj = objective.lower()
        if "git" in obj:
            return self.runtime.registry.get("git").execute(
                operation="status",
                repo_path=str(self.repo_path)
            )
        if "repo" in obj:
            return self.runtime.registry.get("repo").execute(
                operation="tree",
                repo_path=str(self.repo_path)
            )
        if "filesystem" in obj:
            return self.runtime.registry.get("filesystem").execute(
                operation="read",
                path=str(self.repo_path / "test.txt")
            )
        return {"status": "unknown objective"}

    def _analyze_and_fix(self, error: str):
        err = error.lower()
        if "modulenotfounderror" in err:
            return {"type": "git_status"}
        if "unicode" in err:
            return {"type": "filesystem_read_fix", "path": str(self.repo_path / "test.txt")}
        return {"type": "git_status"}

    def _apply_fix(self, fix: dict):
        t = fix["type"]
        if t == "git_status":
            return self.runtime.registry.get("git").execute(
                operation="status",
                repo_path=str(self.repo_path)
            )
        if t == "filesystem_read_fix":
            return self.runtime.registry.get("filesystem").execute(
                operation="read",
                path=fix["path"]
            )
        return {"status": "no_fix_applied"}

    def _commit_changes(self):
        git = self.runtime.registry.get("git")
        git.execute(operation="add", repo_path=str(self.repo_path))
        git.execute(
            operation="commit",
            repo_path=str(self.repo_path),
            message="auto-dev: self-repair execution"
        )

    def _is_success(self, result: Any) -> bool:
        if isinstance(result, dict):
            return "error" not in result and "traceback" not in result
        return True

    def _safe(self, result: Any):
        try:
            return str(result)[:500]
        except:
            return "unserializable"
