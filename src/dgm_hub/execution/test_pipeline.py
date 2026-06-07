import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    success: bool
    output: str
    return_code: int


class TestPipeline:

    def run(
        self,
        command: str,
        cwd: str | Path | None = None
    ) -> TestResult:

        working_dir = Path(cwd).resolve() if cwd else None

        result = subprocess.run(
            command,
            cwd=working_dir,
            shell=True,
            capture_output=True,
            text=True
        )

        return TestResult(
            success=result.returncode == 0,
            output=result.stdout + result.stderr,
            return_code=result.returncode
        )
