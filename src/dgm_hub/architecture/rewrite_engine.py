import shutil
from pathlib import Path
import uuid


class SafeRewriteEngine:

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.backup_path = repo_path / ".arch_backups"

        self.backup_path.mkdir(exist_ok=True)

    def snapshot(self):
        snap_id = str(uuid.uuid4())
        snap_dir = self.backup_path / snap_id
        shutil.copytree(self.repo_path, snap_dir)
        return snap_id

    def rollback(self, snap_id: str):
        snap_dir = self.backup_path / snap_id

        if snap_dir.exists():
            shutil.rmtree(self.repo_path)
            shutil.copytree(snap_dir, self.repo_path)

    def apply_change(self, change: dict):
        """
        Applies safe structural changes.
        """
        # placeholder safe operations only
        return {
            "status": "applied",
            "change": change
        }
