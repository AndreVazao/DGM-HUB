import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    passed: bool
    output: str
    return_code: int

    @property
    def success(self) -> bool:
        return self.passed


class TestPipeline:

    def run(self, command: str | None = None, cwd: str | Path | None = None):
        if not cwd:
            cwd = Path.cwd()
        else:
            cwd = Path(cwd)

        if not command:
            command = "python -m pytest"

        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True
        )

        return TestResult(
            passed=result.returncode == 0,
            output=result.stdout + result.stderr,
            return_code=result.returncode
        )
