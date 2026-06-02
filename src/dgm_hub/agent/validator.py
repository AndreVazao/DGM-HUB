import subprocess
from pathlib import Path


class Validator:

    def __init__(self, repo_path: str):
        self.repo = Path(repo_path)

    # -----------------------------
    # RUN TESTS
    # -----------------------------
    def run_tests(self):

        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "-q"],
                cwd=str(self.repo),
                capture_output=True,
                text=True
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # -----------------------------
    # BASIC HEALTH CHECK
    # -----------------------------
    def repo_health(self):

        issues = []

        if not (self.repo / "src").exists():
            issues.append("missing_src")

        if not (self.repo / "pyproject.toml").exists():
            issues.append("missing_pyproject")

        return {
            "healthy": len(issues) == 0,
            "issues": issues
        }
