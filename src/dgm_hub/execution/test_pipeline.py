import subprocess
from dataclasses import dataclass
from pathlib import Path
import shlex
import logging

LOGGER = logging.getLogger(__name__)


@dataclass
class TestResult:
    passed: bool
    output: str
    return_code: int


class TestPipeline:
    """
    Executes test commands in a specified working directory.
    
    SECURITY: Uses shlex.split() to parse commands safely, preventing
    shell injection. Never uses shell=True.
    """

    def run(
        self,
        command: str | None = None,
        cwd: str | Path | None = None
    ) -> TestResult:
        """
        Run tests in the specified directory.
        
        Args:
            command: Test command to execute (e.g., "python -m pytest -v")
            cwd: Working directory where tests should run
            
        Returns:
            TestResult with pass status, output, and return code
        """
        if command is None:
            command = "python -m pytest"

        working_dir = Path(cwd).resolve() if cwd else Path.cwd()

        # Parse command safely using shlex (prevents shell injection)
        try:
            tokens = shlex.split(command)
        except ValueError as e:
            LOGGER.error(f"Failed to parse test command: {e}")
            return TestResult(
                passed=False,
                output=f"Error parsing command: {e}",
                return_code=-1
            )

        # Execute with list-based invocation (no shell=True)
        result = subprocess.run(
            tokens,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            # NO shell=True - we use a parsed token list instead
        )

        return TestResult(
            passed=result.returncode == 0,
            output=(result.stdout or "") + (result.stderr or ""),
            return_code=result.returncode,
        )
