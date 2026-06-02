import json
from pathlib import Path

from dgm_hub.control.task import Task


class TaskQueue:

    def __init__(self):

        self.root = Path(
            "runtime/tasks"
        )

        self.root.mkdir(
            parents=True,
            exist_ok=True
        )

    def add(self, task: Task):

        path = self.root / f"{task.task_id}.json"

        path.write_text(
            json.dumps(
                task.__dict__,
                indent=2
            )
        )

        return task.task_id

    def get_next(self):

        tasks = sorted(
            self.root.glob("*.json")
        )

        if not tasks:
            return None

        target = tasks[0]

        data = json.loads(
            target.read_text()
        )

        target.unlink()

        return Task(**data)
