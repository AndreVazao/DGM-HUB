from dataclasses import dataclass
from pathlib import Path
from typing import Any
import traceback
import re


@dataclass
class RewriteState:
    objective: str
    success: bool = False
    last_error: str | None = None
    rewrites: int = 0
    history: list[dict] = None

    def __post_init__(self):
        if self.history is None:
            self.history = []


class SelfRewritingEngine:

    def __init__(self, runtime):
        self.runtime = runtime
        self.repo_path = Path("C:\\ProgramasGodMode\\DGM-HUB")

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    def run(self, objective: str, max_cycles: int = 4):

        state = RewriteState(objective=objective)

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

                file_path = self._infer_file(error)

                if file_path:
                    before = self._read_file(file_path)
                    after = self._rewrite(before, error)

                    self._write_file(file_path, after)

                    state.rewrites += 1

                    state.history.append({
                        "cycle": cycle,
                        "file": file_path,
                        "patched": True
                    })

        # commit final
        if state.success:
            self._commit()

        return state

    # -----------------------------
    # EXECUTION
    # -----------------------------
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

        return {"status": "unknown objective"}

    # -----------------------------
    # FILE INFERENCE (CRITICAL PART)
    # -----------------------------
    def _infer_file(self, error: str):

        # module errors
        match = re.search(r"No module named ['\"](.+?)['\"]", error)
        if match:
            module = match.group(1)
            return self.repo_path / "src" / module.replace(".", "/") + ".py"

        # runtime errors pointing to file
        match = re.search(r'File "(.+?\.py)"', error)
        if match:
            return Path(match.group(1))

        return None

    # -----------------------------
    # REWRITE ENGINE (SAFE PATCH ONLY)
    # -----------------------------
    def _rewrite(self, code: str, error: str):

        err = error.lower()

        # FIX 1: missing import
        if "modulenotfounderror" in err:
            match = re.search(r"No module named ['\"](.+?)['\"]", error)
            if match:
                mod = match.group(1)
                return f"import {mod}\n\n" + code

        # FIX 2: simple syntax error fallback
        if "syntaxerror" in err:
            return code.replace("\t", "    ")

        # FIX 3: fallback no-op
        return code

    # -----------------------------
    # FILE IO
    # -----------------------------
    def _read_file(self, path: Path):
        return path.read_text(encoding="utf-8", errors="replace")

    def _write_file(self, path: Path, content: str):
        path.write_text(content, encoding="utf-8")

    # -----------------------------
    # GIT COMMIT
    # -----------------------------
    def _commit(self):

        git = self.runtime.registry.get("git")

        git.execute(
            operation="add",
            repo_path=str(self.repo_path)
        )

        git.execute(
            operation="commit",
            repo_path=str(self.repo_path),
            message="auto-rewrite: self-healing code patch"
        )

    # -----------------------------
    # SUCCESS CHECK
    # -----------------------------
    def _is_success(self, result: Any):

        if isinstance(result, dict):
            return "error" not in result and "traceback" not in result

        return True

    def _safe(self, result: Any):
        try:
            return str(result)[:500]
        except:
            return "unserializable"
