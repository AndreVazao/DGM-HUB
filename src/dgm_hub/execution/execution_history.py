from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExecutionRecord:
    action: str
    timestamp: str
    success: bool


class ExecutionHistory:

    def __init__(self):
        self.records = []

    def add(self, action:str, success:bool):

        self.records.append(
            ExecutionRecord(
                action=action,
                timestamp=datetime.utcnow().isoformat(),
                success=success
            )
        )

    def get(self):
        return self.records
