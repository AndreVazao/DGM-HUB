import subprocess
from pathlib import Path

class Executor:
    def apply_file_changes(self, plan):
        for change in plan.file_changes:
            Path(change.path).write_text(change.diff, encoding="utf-8")

    def run_commands(self, plan):
        for cmd in plan.commands:
            print(f"\nEXEC: {cmd}")
            subprocess.run(cmd, shell=True, check=False)

    def git_commit(self, message="auto commit from DGM-HUB"):
        subprocess.run("git add .", shell=True)
        subprocess.run(f'git commit -m "{message}"', shell=True)
