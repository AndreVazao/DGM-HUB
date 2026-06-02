import json
from pathlib import Path
from datetime import datetime


class MemoryVault:

    def __init__(self, base_path="C:\\AndreOS-Memory"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def write_event(self, event_type: str, data: dict):

        ts = datetime.utcnow().isoformat()

        file = self.base / f"{event_type}.jsonl"

        with file.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": ts,
                "data": data
            }) + "\n")

    def read_events(self, event_type: str):

        file = self.base / f"{event_type}.jsonl"

        if not file.exists():
            return []

        return [
            json.loads(line)
            for line in file.read_text(encoding="utf-8").splitlines()
        ]
