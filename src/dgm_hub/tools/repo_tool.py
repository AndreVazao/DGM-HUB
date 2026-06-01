from pathlib import Path

from dgm_hub.security.path_guard import PathGuard
from dgm_hub.tools.base import Tool
from dgm_hub.execution.command_runner import CommandRunner


class RepoTool(Tool):
    name = "repo"

    def __init__(self, guard: PathGuard):
        self.guard = guard
        self.runner = CommandRunner()

    def execute(self, operation: str, repo_path: str):
        if not self.guard.is_allowed(repo_path):
            raise PermissionError(f"Path denied: {repo_path}")

        repo = Path(repo_path)

        if operation == "status":
            return self.runner.run(["git", "-C", str(repo), "status", "--short"])

        if operation == "pull":
            return self.runner.run(["git", "-C", str(repo), "pull"])

        raise ValueError("Unsupported repo operation")