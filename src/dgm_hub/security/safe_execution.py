from dataclasses import dataclass
from pathlib import Path
import shutil
import uuid

@dataclass
class ExecutionSnapshot:
    snapshot_id: str
    path: str
    backup_path: str

class SafeExecutionManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.snapshots_dir = self.base_dir.parent / ".dgm_snapshots" / self.base_dir.name
        self.snapshots_dir.mkdir(exist_ok=True, parents=True)

    def create_snapshot(self, target_path: str) -> ExecutionSnapshot:
        snapshot_id = str(uuid.uuid4())
        backup_path = self.snapshots_dir / snapshot_id
        shutil.copytree(target_path, backup_path)
        return ExecutionSnapshot(
            snapshot_id=snapshot_id,
            path=target_path,
            backup_path=str(backup_path)
        )

    def rollback(self, snapshot: ExecutionSnapshot):
        target = Path(snapshot.path)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(snapshot.backup_path, target)
