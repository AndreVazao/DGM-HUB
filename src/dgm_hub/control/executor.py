import subprocess
import shlex
from pathlib import Path
import logging

LOGGER = logging.getLogger(__name__)


class Executor:
    """
    Executes file changes and commands safely.
    
    SECURITY: All subprocess calls use list-based invocation
    instead of shell=True to prevent injection.
    """
    
    def apply_file_changes(self, plan):
        """Apply file changes from plan."""
        for change in plan.file_changes:
            Path(change.path).write_text(change.diff, encoding="utf-8")

    def run_commands(self, plan):
        """Execute commands from plan safely."""
        for cmd in plan.commands:
            LOGGER.info(f"EXEC: {cmd}")
            try:
                # Parse command safely
                tokens = shlex.split(cmd)
                # Execute without shell=True
                result = subprocess.run(
                    tokens,
                    check=False,
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    LOGGER.info(result.stdout)
                if result.stderr:
                    LOGGER.error(result.stderr)
            except ValueError as e:
                LOGGER.error(f"Failed to parse command '{cmd}': {e}")

    def git_commit(self, message="auto commit from DGM-HUB"):
        """Commit changes to git safely."""
        try:
            # Use list-based git commands
            subprocess.run(
                ["git", "add", "."],
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True
            )
            LOGGER.info(f"Git commit: {message}")
        except subprocess.CalledProcessError as e:
            LOGGER.error(f"Git commit failed: {e}")
