from dataclasses import dataclass
from pathlib import Path
import shutil
import uuid
import hashlib

@dataclass
class ExecutionSnapshot:
    snapshot_id: str
    path: str
    backup_path: str

class SafeExecutionManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        # Use a global runtime directory outside the repo
        repo_hash = hashlib.md5(str(self.base_dir).encode()).hexdigest()[:8]
        self.snapshots_dir = Path("runtime/snapshots") / f"{self.base_dir.name}_{repo_hash}"
        self.snapshots_dir.mkdir(exist_ok=True, parents=True)

    def create_snapshot(self, target_path: str) -> ExecutionSnapshot:
        snapshot_id = str(uuid.uuid4())
        backup_path = self.snapshots_dir / snapshot_id

        target = Path(target_path)
        if not target.is_absolute():
            target = (self.base_dir / target).resolve()

        if target.is_dir():
            shutil.copytree(str(target), str(backup_path))
        else:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(target), str(backup_path))

        return ExecutionSnapshot(
            snapshot_id=snapshot_id,
            path=str(target),
            backup_path=str(backup_path)
        )

    def rollback(self, snapshot: ExecutionSnapshot):
        target = Path(snapshot.path)
        backup = Path(snapshot.backup_path)
        if target.is_dir():
            if target.exists():
                shutil.rmtree(str(target))
            shutil.copytree(str(backup), str(target))
        else:
            shutil.copy2(str(backup), str(target))
