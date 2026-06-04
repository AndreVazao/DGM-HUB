import json
from pathlib import Path
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone


class ExecutionJournal:

    def __init__(self, path: str | Path = "runtime/execution_journal.jsonl"):
        self.file = Path(path)
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

    def log_task_execution(self, repository_path: str, result):
        payload = {
            "type": "task_execution",
            "repository_path": repository_path,
            "result": self._to_jsonable(result),
            "timestamp": str(datetime.now(timezone.utc))
        }

        with self.file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

    def _to_jsonable(self, value):
        if is_dataclass(value):
            return self._to_jsonable(asdict(value))
        if isinstance(value, dict):
            return {k: self._to_jsonable(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._to_jsonable(v) for v in value]
        return value
