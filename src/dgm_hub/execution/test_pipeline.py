import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    passed: bool
    output: str
    return_code: int


class TestPipeline:

    def run(self, repo_path: str | Path, command: str | None = None):
        cwd = Path(repo_path)

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
