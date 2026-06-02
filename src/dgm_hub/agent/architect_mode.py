from dataclasses import dataclass
from pathlib import Path
from typing import Any
import traceback
import json


@dataclass
class ArchitectState:
    objective: str
    success: bool = False
    errors: list[str] = None
    fixes: int = 0
    plan: dict = None
    history: list[dict] = None

    def __post_init__(self):
        self.errors = self.errors or []
        self.history = self.history or []
        self.plan = self.plan or {}


class ArchitectEngine:

    def __init__(self, runtime):
        self.runtime = runtime
        self.repo_path = Path("C:\\ProgramasGodMode\\DGM-HUB")

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    def run(self, objective: str = "architect audit", max_cycles: int = 3):

        state = ArchitectState(objective=objective)

        for cycle in range(max_cycles):

            try:
                # 1. analyze full repo structure
                structure = self._analyze_repo()

                # 2. build architecture map
                state.plan = self._build_architecture_map(structure)

                # 3. validate system coherence
                issues = self._detect_issues(state.plan)

                if not issues:
                    state.success = True
                    break

                # 4. apply fixes
                for issue in issues:
                    self._apply_fix(issue)
                    state.fixes += 1

                state.history.append({
                    "cycle": cycle,
                    "issues": issues
                })

            except Exception:
                state.errors.append(traceback.format_exc())

        # final commit if improved
        if state.fixes > 0:
            self._commit()

        return state

    # -----------------------------
    # REPO ANALYSIS
    # -----------------------------
    def _analyze_repo(self):

        repo = self.runtime.registry.get("repo")

        return repo.execute(
            operation="tree",
            repo_path=str(self.repo_path)
        )

    # -----------------------------
    # ARCHITECTURE MAPPER
    # -----------------------------
    def _build_architecture_map(self, structure: dict):

        return {
            "modules": self._extract_modules(structure),
            "tools": self.runtime.registry.list_tools(),
            "entrypoints": ["main.py"],
        }

    def _extract_modules(self, tree):

        modules = []

        def walk(node, prefix=""):
            if node["type"] == "file":
                if node["name"].endswith(".py"):
                    modules.append(prefix + node["name"])
            else:
                for c in node.get("children", []):
                    walk(c, prefix + node["name"] + ".")

        walk(tree["tree"])
        return modules

    # -----------------------------
    # ISSUE DETECTION
    # -----------------------------
    def _detect_issues(self, plan: dict):

        issues = []

        # rule 1: missing critical modules
        required = ["main.py", "runtime.py", "bootstrap.py"]

        for r in required:
            if not any(r in m for m in plan["modules"]):
                issues.append({
                    "type": "missing_core_module",
                    "target": r
                })

        # rule 2: no git tool registered
        if "git" not in plan["tools"]:
            issues.append({
                "type": "missing_tool",
                "tool": "git"
            })

        return issues

    # -----------------------------
    # FIX ENGINE
    # -----------------------------
    def _apply_fix(self, issue: dict):

        t = issue["type"]

        if t == "missing_tool":

            # safe remediation: log only (no auto injection yet)
            print(f"[ARCHITECT] missing tool: {issue['tool']}")

        if t == "missing_core_module":

            # scaffold warning only (safe mode)
            print(f"[ARCHITECT] missing module detected: {issue['target']}")

    # -----------------------------
    # COMMIT
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
            message="architect mode: structural audit & adjustments"
        )
