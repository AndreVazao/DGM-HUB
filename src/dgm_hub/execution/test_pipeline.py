import subprocess
from dataclasses import dataclass


@dataclass
class TestResult:
    success: bool
    output: str
    return_code: int


class TestPipeline:

    def run(self, command: str):

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        return TestResult(
            success=result.returncode == 0,
            output=result.stdout + result.stderr,
            return_code=result.returncode
        )
