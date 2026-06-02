from dataclasses import dataclass, field
from pathlib import Path
import traceback
import json
import re


@dataclass
class CognitiveState:
    objective: str
    success: bool = False
    steps: list = field(default_factory=list)
    memory: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    fixes: int = 0


class CognitiveAgent:

    def __init__(self, runtime):
        self.runtime = runtime
        self.repo = Path("C:\\ProgramasGodMode\\DGM-HUB")

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    def run(self, objective: str, max_iters: int = 6):

        state = CognitiveState(objective=objective)

        for i in range(max_iters):

            step = {"iteration": i}

            try:
                # 1. PLAN
                plan = self._plan(objective, state)
                step["plan"] = plan

                # 2. EXECUTE
                result = self._execute(plan)
                step["result"] = self._safe(result)

                # 3. CHECK SUCCESS
                if self._is_success(result):
                    state.success = True
                    state.steps.append(step)
                    break

            except Exception as e:

                error = traceback.format_exc()
                step["error"] = error

                # 4. DIAGNOSE
                diagnosis = self._diagnose(error)
                step["diagnosis"] = diagnosis

                # 5. FIX
                fix_result = self._apply_fix(diagnosis)
                step["fix"] = fix_result

                state.fixes += 1

            state.steps.append(step)

        # persist memory
        self._store_memory(state)

        # commit if successful
        if state.success:
            self._commit()

        return state

    # -----------------------------
    # PLANNING
    # -----------------------------
    def _plan(self, objective, state):

        obj = objective.lower()

        if "git" in obj:
            return {"tool": "git", "operation": "status"}

        if "repo" in obj:
            return {"tool": "repo", "operation": "tree"}

        if "filesystem" in obj:
            return {
                "tool": "filesystem",
                "operation": "read",
                "path": "C:\\AI\\test.txt"
            }

        return {"tool": "git", "operation": "status"}

    # -----------------------------
    # EXECUTION
    # -----------------------------
    def _execute(self, plan):

        tool = self.runtime.registry.get(plan["tool"])

        if not tool:
            raise Exception(f"Tool not found: {plan['tool']}")

        args = dict(plan)
        args.pop("tool", None)

        return tool.execute(**args)

    # -----------------------------
    # DIAGNOSIS ENGINE (CEREBRO)
    # -----------------------------
    def _diagnose(self, error: str):

        err = error.lower()

        if "modulenotfounderror" in err:
            match = re.search(r"No module named ['\"](.+?)['\"]", error)
            return {
                "type": "missing_module",
                "module": match.group(1) if match else None
            }

        if "permission" in err:
            return {"type": "permission_issue"}

        if "unicode" in err:
            return {"type": "encoding_issue"}

        return {"type": "unknown"}

    # -----------------------------
    # SELF-REPAIR ENGINE
    # -----------------------------
    def _apply_fix(self, diagnosis):

        t = diagnosis["type"]

        if t == "missing_module":
            module = diagnosis.get("module")
            return self._inject_import(module)

        if t == "encoding_issue":
            return {"action": "retry_with_utf8"}

        if t == "permission_issue":
            return {"action": "adjust_path_policy"}

        return {"action": "no_fix"}

    # -----------------------------
    # CODE PATCHING (SAFE MODE)
    # -----------------------------
    def _inject_import(self, module):

        if not module:
            return {"status": "no_module"}

        file_path = self.repo / "src" / (module.replace(".", "/") + ".py")

        if not file_path.exists():
            return {"status": "file_not_found", "path": str(file_path)}

        code = file_path.read_text(encoding="utf-8", errors="ignore")

        patched = f"import {module}\n\n" + code

        file_path.write_text(patched, encoding="utf-8")

        return {"status": "patched", "file": str(file_path)}

    # -----------------------------
    # MEMORY
    # -----------------------------
    def _store_memory(self, state):

        mem_file = self.repo / "docs/context/agent_memory.json"

        mem_file.parent.mkdir(parents=True, exist_ok=True)

        existing = {}

        if mem_file.exists():
            try:
                existing = json.loads(mem_file.read_text())
            except:
                existing = {}

        existing[state.objective] = {
            "success": state.success,
            "fixes": state.fixes
        }

        mem_file.write_text(json.dumps(existing, indent=2))

    # -----------------------------
    # GIT COMMIT
    # -----------------------------
    def _commit(self):

        git = self.runtime.registry.get("git")

        git.execute(
            operation="add",
            repo_path=str(self.repo)
        )

        git.execute(
            operation="commit",
            repo_path=str(self.repo),
            message="cognitive agent: autonomous engineering iteration"
        )

    # -----------------------------
    # UTIL
    # -----------------------------
    def _is_success(self, result):
        if isinstance(result, dict):
            return "error" not in result and "traceback" not in result
        return True

    def _safe(self, r):
        return str(r)[:400]
