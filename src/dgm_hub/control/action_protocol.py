from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Action:
    type: str   # edit_file | run_command | git | test
    payload: Dict[str, Any]

@dataclass
class ExecutionPlan:
    id: str
    title: str
    summary: str
    actions: List[Action]
    risk: str
