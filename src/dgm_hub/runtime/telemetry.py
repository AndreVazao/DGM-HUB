import json
from datetime import datetime
from pathlib import Path

class Telemetry:
    def __init__(self):
        self.file = Path("runtime/telemetry.jsonl")
        self.file.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: str, data: dict):
        entry = {
            "time": datetime.utcnow().isoformat(),
            "event": event,
            "data": data
        }
        with self.file.open("a") as f:
            f.write(json.dumps(entry) + "\n")
