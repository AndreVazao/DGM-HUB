from dataclasses import dataclass
from typing import List

@dataclass
class FileChange:
    path: str
    diff: str

@dataclass
class ExecutionPlan:
    summary: str
    file_changes: List[FileChange]
    commands: List[str]
    risk_level: str
