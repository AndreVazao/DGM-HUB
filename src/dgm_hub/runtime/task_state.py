import json
from pathlib import Path

class TaskStateStore:
    def __init__(self, file="runtime/task_state.json"):
        self.file = Path(file)
        self.file.parent.mkdir(exist_ok=True, parents=True)
        if not self.file.exists():
            self.file.write_text("[]")

    def save(self, state: dict):
        data = json.loads(self.file.read_text())
        data.append(state)
        self.file.write_text(json.dumps(data, indent=2))

    def load(self):
        return json.loads(self.file.read_text())
