from dataclasses import dataclass
from pathlib import Path
import json
import hashlib
import time
import subprocess


@dataclass
class TruthSnapshot:
    id: str
    repo_path: str
    git_head: str
    timestamp: float
    file_hashes: dict


class TruthLayer:
    """
    Single Source of Truth for all execution validation.
    Prevents fake success states in agent runs.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.snapshots_path = self.repo_path / ".dgm_truth"
        self.snapshots_path.mkdir(exist_ok=True)

    # ---------------------------
    # SNAPSHOT
    # ---------------------------

    def create_snapshot(self) -> TruthSnapshot:
        git_head = self._git_head()

        file_hashes = self._hash_repo_files()

        snapshot = TruthSnapshot(
            id=str(int(time.time() * 1000)),
            repo_path=str(self.repo_path),
            git_head=git_head,
            timestamp=time.time(),
            file_hashes=file_hashes
        )

        self._save(snapshot)
        return snapshot

    # ---------------------------
    # VERIFY
    # ---------------------------

    def verify_snapshot(self, snapshot: TruthSnapshot) -> dict:
        current_head = self._git_head()
        current_hashes = self._hash_repo_files()

        drift_files = []

        for path, h in snapshot.file_hashes.items():
            if path not in current_hashes or current_hashes[path] != h:
                drift_files.append(path)

        return {
            "git_head_changed": current_head != snapshot.git_head,
            "drift_files": drift_files,
            "integrity_ok": len(drift_files) == 0 and current_head == snapshot.git_head
        }

    # ---------------------------
    # INTERNALS
    # ---------------------------

    def _git_head(self) -> str:
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path
            ).decode().strip()
        except Exception:
            return "unknown"

    def _hash_repo_files(self) -> dict:
        result = {}

        for path in self.repo_path.rglob("*"):
            if not path.is_file():
                continue

            if ".git" in str(path):
                continue

            if ".dgm_truth" in str(path):
                continue

            try:
                data = path.read_bytes()
                result[str(path.relative_to(self.repo_path))] = hashlib.sha256(data).hexdigest()
            except Exception:
                continue

        return result

    def _save(self, snapshot: TruthSnapshot):
        file_path = self.snapshots_path / f"{snapshot.id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(snapshot.__dict__, f, indent=2)
