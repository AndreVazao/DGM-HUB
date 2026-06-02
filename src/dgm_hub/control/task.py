from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Task:
    objective: str
    priority: int = 1
    status: str = "queued"
    task_id: str = field(
        default_factory=lambda:
        str(uuid.uuid4())[:8]
    )
    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )
    result: dict | None = None
    error: str | None = None
