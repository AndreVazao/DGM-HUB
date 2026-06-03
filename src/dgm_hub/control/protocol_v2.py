from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Action:
    type: str
    payload: Dict[str, Any]

@dataclass
class ExecutionPlan:
    id: str
    title: str
    summary: str
    actions: List[Action]
    risk: str
