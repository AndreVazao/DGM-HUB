from collections import defaultdict
import json
from pathlib import Path


class EvolutionLoop:
    """
    Observa execução do sistema e propõe upgrades estruturais.
    NÃO executa mudanças diretamente.
    Apenas gera patches.
    """

    def __init__(self, memory_path="runtime/memory.json"):
        self.memory_path = Path(memory_path)
        self.failure_patterns = defaultdict(int)
        self.success_patterns = defaultdict(int)

    # -------------------------
    # LOAD MEMORY
    # -------------------------
    def _load(self):
        if not self.memory_path.exists():
            return []

        try:
            return json.loads(self.memory_path.read_text())
        except:
            return []

    # -------------------------
    # ANALYZE EXECUTION HISTORY
    # -------------------------
    def analyze(self):

        data = self._load()

        for entry in data:

            obj = entry.get("objective", "unknown")
            success = entry.get("success", False)

            if success:
                self.success_patterns[obj] += 1
            else:
                self.failure_patterns[obj] += 1

        return {
            "success": dict(self.success_patterns),
            "failure": dict(self.failure_patterns)
        }

    # -------------------------
    # DETECT SYSTEMIC ISSUES
    # -------------------------
    def detect_issues(self):

        issues = []

        for obj, count in self.failure_patterns.items():

            if count >= 3:
                issues.append({
                    "type": "repeated_failure",
                    "objective": obj,
                    "severity": "high"
                })

        return issues

    # -------------------------
    # GENERATE PATCH PROPOSALS
    # -------------------------
    def propose_patches(self, issues):

        patches = []

        for issue in issues:

            if issue["type"] == "repeated_failure":

                patches.append({
                    "target": "agent.cognitive_engine",
                    "action": "refactor_execution_strategy",
                    "reason": issue["objective"],
                    "risk": "medium"
                })

        return patches
