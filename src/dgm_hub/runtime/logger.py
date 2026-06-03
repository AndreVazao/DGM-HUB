import json
from datetime import datetime
from pathlib import Path

class RuntimeLogger:
    def __init__(self, log_file="runtime/logs.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, data: dict):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data
        }
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
