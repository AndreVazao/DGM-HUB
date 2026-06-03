import json
from pathlib import Path
from datetime import datetime, timezone


class ExecutionJournal:

    def __init__(self):
        self.file = Path("runtime/execution_journal.jsonl")
        self.file.parent.mkdir(parents=True, exist_ok=True)

    def log_plan(self, plan):
        entry = {
            "type": "plan",
            "id": getattr(plan, "id", "unknown"),
            "title": getattr(plan, "title", "unknown"),
            "summary": getattr(plan, "summary", "unknown"),
            "risk": getattr(plan, "risk", "unknown"),
            "actions": [a.__dict__ if hasattr(a, "__dict__") else str(a) for a in getattr(plan, "actions", [])],
            "timestamp": str(datetime.now(timezone.utc))
        }

        with self.file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def log_result(self, plan_id: str, result: dict):
        entry = {
            "type": "result",
            "plan_id": plan_id,
            "result": result,
            "timestamp": str(datetime.now(timezone.utc))
        }

        with self.file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
