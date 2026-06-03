import json
from pathlib import Path


class RecoveryEngine:
    def __init__(self):
        self.file = Path("runtime/execution_journal.jsonl")

    def recover_last_state(self):
        if not self.file.exists():
            return []

        lines = self.file.read_text(encoding="utf-8").splitlines()
        return [json.loads(l) for l in lines[-50:]]
