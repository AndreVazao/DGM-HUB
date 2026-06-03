import json
from pathlib import Path

class LiveLogStream:
    def __init__(self):
        self.file = Path("runtime/live.log")
        self.file.parent.mkdir(exist_ok=True, parents=True)

    def write(self, event: str, data: dict):
        with self.file.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "event": event,
                "data": data
            }) + "\n")
