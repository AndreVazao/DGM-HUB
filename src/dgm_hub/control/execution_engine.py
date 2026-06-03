import subprocess
from pathlib import Path

class ExecutionEngine:
    def execute(self, plan):
        for action in plan.actions:
            if action.type == "edit_file":
                path = Path(action.payload["path"])
                path.write_text(action.payload["content"], encoding="utf-8")
            elif action.type == "run_command":
                subprocess.run(action.payload["cmd"], shell=True, check=False)
            elif action.type == "git":
                subprocess.run(action.payload["cmd"], shell=True)
            elif action.type == "test":
                subprocess.run(action.payload["cmd"], shell=True)
