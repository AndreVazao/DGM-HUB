import json
from pathlib import Path
from dataclasses import is_dataclass, asdict


class ExecutionMemory:
    """
    Stores execution history that influences future decisions
    """

    def __init__(self, path="runtime/memory.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.write_text("[]")

    def _serialize(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, list):
            return [self._serialize(i) for i in obj]
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        return obj

    def log(self, entry: dict):
        data = json.loads(self.path.read_text())
        serialized_entry = self._serialize(entry)
        data.append(serialized_entry)
        self.path.write_text(json.dumps(data, indent=2))

    def load(self):
        return json.loads(self.path.read_text())
