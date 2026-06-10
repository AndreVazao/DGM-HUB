from pathlib import Path
import subprocess
import sys
import shlex

from dgm_hub.security.policy_engine import PolicyEngine
from dgm_hub.security.command_validator import CommandValidator
from dgm_hub.runtime.live_logs import LOGGER


class ExecutionEngine:
    def __init__(self, base_dir: str | Path = ".", timeout_seconds: int | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.policy = PolicyEngine()
        self.command_validator = CommandValidator(allowed_base_paths=[self.base_dir])
        self.timeout_seconds = timeout_seconds

    def execute(self, plan, journal=None):
        if journal:
            journal.log_plan(plan)

        results = []
        plan_id = getattr(plan, "id", "unknown")

        for action in plan.actions:
            try:
                if action.type == "edit_file":
                    raw_path = action.payload["path"]
                    if not self.policy.validate_path_within(raw_path, self.base_dir):
                        raise PermissionError(f"Path denied: {raw_path}")

                    path = self._resolve_path(raw_path)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(action.payload["content"], encoding="utf-8")
                    LOGGER.log(f"Edited file: {raw_path}")
                elif action.type in ["run_command", "git", "test"]:
                    LOGGER.log(f"Executing {action.type}: {action.payload['cmd']}")
                    command_result = self._run_command(action.payload["cmd"])
                    if command_result["returncode"] != 0:
                        results.append({
                            "action": action.type,
                            "status": "error",
                            "command": command_result,
                            "error": f"Command failed with return code {command_result['returncode']}"
                        })
                        del command_result
                        continue
                elif action.type == "internal_call":
                    # Mock action for pure engine benchmarking. No subprocess is spawned.
                    if action.payload.get("simulate_error"):
                        results.append({
                            "action": action.type,
                            "status": "error",
                            "error": "Simulated error"
                        })
                        continue
                    else:
                        # Just pass through to successful result
                        pass
                else:
                    if hasattr(action, "payload") and "cmd" in action.payload:
                        LOGGER.log(f"Executing {action.type}: {action.payload['cmd']}")
                        command_result = self._run_command(action.payload["cmd"])
                        results.append({
                            "action": action.type,
                            "status": "ok" if command_result["returncode"] == 0 else "error",
                            "command": command_result
                        })
                        continue

                results.append({
                    "action": action.type,
                    "status": "ok",
                })
            except PermissionError as e:
                LOGGER.log(f"[ERROR] Permission denied: {e}")
                results.append({
                    "action": action.type,
                    "status": "error",
                    "error": str(e)
                })
            except Exception as e:
                LOGGER.log(f"[ERROR] Action failed: {e}")
                results.append({
                    "action": action.type,
                    "status": "error",
                    "error": str(e)
                })

        return results

    def _resolve_path(self, path: str) -> Path:
        raw = Path(path)
        return raw.resolve() if raw.is_absolute() else (self.base_dir / raw).resolve()

    def _run_command(self, command: str) -> dict:
        """
        Execute a command safely without shell injection risks.
        
        SECURITY:
        - Uses CommandValidator for security checks
        - Uses shlex.split() for proper command parsing
        - Uses list-based subprocess.Popen (no shell=True)
        - Validates against dangerous patterns and operators
        
        Args:
            command: The command string to execute
            
        Returns:
            Dictionary with returncode, stdout, stderr
            
        Raises:
            PermissionError: If command is not allowed by policy
        """
        # Validate command security
        if not self.command_validator.is_safe(command):
            raise PermissionError(f"Command rejected by security policy: {command}")
        
        # Additional legacy validation (for compatibility)
        if not self.policy.validate_command(command):
            raise PermissionError(f"Command denied by policy: {command}")
        
        # Parse command safely
        try:
            tokens = shlex.split(command)
            if not tokens:
                raise ValueError("Empty command")
        except ValueError as e:
            raise PermissionError(f"Invalid command syntax: {e}")

        # Use Popen so we can forcefully kill on Windows when timeout fires.
        # subprocess.run(..., timeout=N) with shell=True on Windows raises
        # TimeoutExpired but does NOT kill the child process tree, causing
        # communicate() to hang indefinitely.
        #
        # CRITICAL FIX: Use list-based invocation (tokens) instead of shell=True
        # This prevents shell injection entirely. The command is parsed by shlex,
        # not by the shell, so no shell metacharacters are evaluated.
        kwargs = dict(
            cwd=str(self.base_dir),
            # NO shell=True - we pass a list of tokens instead
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        try:
            proc = subprocess.Popen(tokens, **kwargs)
            stdout_bytes, stderr_bytes = proc.communicate(timeout=self.timeout_seconds)
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            if stdout:
                LOGGER.log(stdout)
            if stderr:
                LOGGER.log(stderr)

            return {
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
        except subprocess.TimeoutExpired:
            # Kill the whole process group / tree on Windows
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                )
            else:
                proc.kill()
            # Drain remaining output so the process is fully reaped
            try:
                stdout_bytes, stderr_bytes = proc.communicate(timeout=5)
            except Exception:
                stdout_bytes, stderr_bytes = b"", b""

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            if stdout:
                LOGGER.log(stdout)
            if stderr:
                LOGGER.log(stderr)

            return {
                "returncode": -1,
                "stdout": stdout,
                "stderr": f"Command timed out after {self.timeout_seconds}s\n{stderr}",
            }
