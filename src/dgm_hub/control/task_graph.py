from dataclasses import dataclass, field
from typing import List, Optional, Any
import uuid


@dataclass
class TaskNode:
    id: str
    objective: str
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Any = None


class TaskGraph:
    """
    Tracks evolution of tasks (civilization memory structure)
    """

    def __init__(self):
        self.nodes: dict[str, TaskNode] = {}

    def create_task(self, objective: str, parent: str | None = None) -> str:

        task_id = str(uuid.uuid4())[:8]

        node = TaskNode(
            id=task_id,
            objective=objective,
            parent=parent
        )

        self.nodes[task_id] = node

        if parent and parent in self.nodes:
            self.nodes[parent].children.append(task_id)

        return task_id

    def update(self, task_id: str, status: str, result=None):
        if task_id not in self.nodes:
            return

        self.nodes[task_id].status = status
        self.nodes[task_id].result = result
