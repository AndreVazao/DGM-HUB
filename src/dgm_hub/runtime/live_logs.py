import json
from pathlib import Path
from dgm_hub.ui.state import STATE

class LiveLogStream:
    def __init__(self):
        self.file = Path("runtime/live.log")
        self.file.parent.mkdir(exist_ok=True, parents=True)

    def write(self, event: str, data: dict):
        try:
            with self.file.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "event": event,
                    "data": data
                }) + "\n")
        except Exception:
            pass

        try:
            if event == "log":
                message = data.get("message", "")
                STATE.add_log(message)
            else:
                STATE.add_log(f"[{event}] {json.dumps(data)}")
        except Exception:
            pass

    def log(self, message: str):
        self.write("log", {"message": message})

LOGGER = LiveLogStream()
