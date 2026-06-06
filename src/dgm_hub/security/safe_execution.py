from dataclasses import dataclass
from pathlib import Path
import shutil
import uuid
import hashlib
import subprocess
import logging

@dataclass
class ExecutionSnapshot:
    snapshot_id: str
    path: str
    backup_path: str | None = None
    is_git: bool = False

class SafeExecutionManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        repo_hash = hashlib.md5(str(self.base_dir).encode()).hexdigest()[:8]
        self.snapshots_dir = Path("runtime/snapshots") / f"{self.base_dir.name}_{repo_hash}"
        self.snapshots_dir.mkdir(exist_ok=True, parents=True)

    def _is_git_repo(self, path: Path) -> bool:
        return (path / ".git").is_dir()

    def create_snapshot(self, target_path: str) -> ExecutionSnapshot:
        snapshot_id = str(uuid.uuid4())
        target = Path(target_path)
        if not target.is_absolute():
            target = (self.base_dir / target).resolve()

        if self._is_git_repo(target):
            # Check if there are any files tracked by git
            result = subprocess.run(["git", "ls-files"], cwd=target, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                # Fast git-based snapshot
                return ExecutionSnapshot(
                    snapshot_id=snapshot_id,
                    path=str(target),
                    backup_path=None,
                    is_git=True
                )

        # Fallback to copy-based snapshot
        backup_path = self.snapshots_dir / snapshot_id
        if target.is_dir():
            shutil.copytree(str(target), str(backup_path))
        else:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(target), str(backup_path))

        return ExecutionSnapshot(
            snapshot_id=snapshot_id,
            path=str(target),
            backup_path=str(backup_path),
            is_git=False
        )

    def rollback(self, snapshot: ExecutionSnapshot):
        target = Path(snapshot.path)
        if snapshot.is_git:
            try:
                # Clean untracked files and reset changes
                subprocess.run(["git", "clean", "-fd"], cwd=target, check=True, capture_output=True)
                subprocess.run(["git", "checkout", "."], cwd=target, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Git rollback failed: {e.stderr.decode() if e.stderr else str(e)}")
            return

        if not snapshot.backup_path:
            return

        backup = Path(snapshot.backup_path)
        if target.is_dir():
            if target.exists():
                shutil.rmtree(str(target))
            shutil.copytree(str(backup), str(target))
        else:
            shutil.copy2(str(backup), str(target))
