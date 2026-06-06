from pathlib import Path
import subprocess
import sys

from dgm_hub.security.policy_engine import PolicyEngine
from dgm_hub.runtime.live_logs import LOGGER


class ExecutionEngine:
    def __init__(self, base_dir: str | Path = ".", timeout_seconds: int | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.policy = PolicyEngine()
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
                        if command_result["returncode"] != 0:
                            results.append({
                                "action": action.type,
                                "status": "error",
                                "command": command_result,
                                "error": f"Command failed with return code {command_result['returncode']}"
                            })
                            del command_result
                            continue
                    else:
                        results.append({"action": action.type, "status": "error", "error": f"Unknown action type: {action.type}"})
                        continue

                result = {"action": action.type, "status": "ok"}
                if action.type in ["run_command", "git", "test"] or "command_result" in locals():
                    result["command"] = command_result
                    del command_result
                results.append(result)
            except Exception as e:
                results.append({"action": action.type, "status": "error", "error": str(e)})

        if journal:
            journal.log_result(plan_id, {"results": results})

        return results

    def _resolve_path(self, path: str) -> Path:
        raw = Path(path)
        return raw.resolve() if raw.is_absolute() else (self.base_dir / raw).resolve()

    def _run_command(self, command: str) -> dict:
        if not self.policy.validate_command(command):
            raise PermissionError(f"Command denied: {command}")

        # Use Popen so we can forcefully kill on Windows when timeout fires.
        # subprocess.run(..., timeout=N) with shell=True on Windows raises
        # TimeoutExpired but does NOT kill the child process tree, causing
        # communicate() to hang indefinitely.
        kwargs = dict(
            cwd=self.base_dir,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        proc = subprocess.Popen(command, **kwargs)
        try:
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
