import subprocess
from pathlib import Path

from dgm_hub.security.path_guard import PathGuard
from dgm_hub.tools.base import Tool


class GitTool(Tool):

    name = "git"

    def __init__(
        self,
        guard: PathGuard
    ):
        self.guard = guard

    # ---------------------------------
    # INTERNAL EXECUTOR
    # ---------------------------------

    def _run(
        self,
        repo: Path,
        args: list[str]
    ):

        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        operation: str,
        repo_path: str,
        message: str | None = None,
        branch: str | None = None
    ):

        if not self.guard.is_allowed(
            repo_path
        ):
            raise PermissionError(
                f"Path denied: {repo_path}"
            )

        repo = Path(repo_path)

        if not repo.exists():
            raise ValueError(
                f"Repo not found: {repo_path}"
            )

        # -------------------------
        # STATUS
        # -------------------------

        if operation == "status":

            return self._run(
                repo,
                ["status", "--short"]
            )

        # -------------------------
        # ADD
        # -------------------------

        if operation == "add":

            return self._run(
                repo,
                ["add", "-A"]
            )

        # -------------------------
        # COMMIT
        # -------------------------

        if operation == "commit":

            if not message:
                raise ValueError(
                    "commit requires message"
                )

            return self._run(
                repo,
                [
                    "commit",
                    "-m",
                    message
                ]
            )

        # -------------------------
        # PUSH
        # -------------------------

        if operation == "push":

            args = ["push"]

            if branch:

                args += [
                    "origin",
                    branch
                ]

            return self._run(
                repo,
                args
            )

        # -------------------------
        # PULL
        # -------------------------

        if operation == "pull":

            args = [
                "pull",
                "--rebase"
            ]

            if branch:

                args += [
                    "origin",
                    branch
                ]

            return self._run(
                repo,
                args
            )

        # -------------------------
        # LOG
        # -------------------------

        if operation == "log":

            return self._run(
                repo,
                [
                    "log",
                    "--oneline",
                    "-n",
                    "20"
                ]
            )

        raise ValueError(
            f"Unsupported git operation: {operation}"
        )
