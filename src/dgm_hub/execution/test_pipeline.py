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
        command: str | None = None,
        cwd: str | Path | None = None
    ) -> TestResult:

        if command is None:
            command = "python -m pytest"

        working_dir = Path(cwd).resolve() if cwd else Path.cwd()

        result = subprocess.run(
            command,
            cwd=str(working_dir),
            shell=True,
            capture_output=True,
            text=True,
        )

        return TestResult(
            success=result.returncode == 0,
            output=(result.stdout or "") + (result.stderr or ""),
            return_code=result.returncode,
        )
