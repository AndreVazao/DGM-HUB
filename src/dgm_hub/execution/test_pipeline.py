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

    def run(
        self,
        arg1: str | Path,
        command: str | None = None,
        cwd: str | Path | None = None,
    ) -> TestResult:

        try:

            # Legacy API:
            # run(repo_path, command)

            if command is not None and cwd is None:

                repo_path = Path(arg1)

                cmd = command

            else:

                # Modern API:
                # run(command, cwd=repo)

                cmd = str(arg1)

                repo_path = Path(cwd) if cwd else Path.cwd()

            result = subprocess.run(
                cmd,
                cwd=repo_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return TestResult(
                passed=result.returncode == 0,
                output=(result.stdout or "") + (result.stderr or ""),
                return_code=result.returncode,
            )

        except subprocess.TimeoutExpired:

            return TestResult(
                passed=False,
                output="Test execution timeout",
                return_code=-1,
            )

        except Exception as exc:

            return TestResult(
                passed=False,
                output=str(exc),
                return_code=-1,
            )
