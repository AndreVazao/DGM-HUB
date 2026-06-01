from pathlib import Path
from datetime import datetime
import json


class AuditLogger:
    def __init__(self, path: str = "logs/audit"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, data: dict):
        file = self.path / "audit.jsonl"

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data,
        }

        with open(file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
