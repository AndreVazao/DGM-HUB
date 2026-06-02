import subprocess
import hashlib
from pathlib import Path
import json
import difflib


class ActivePatchEngine:
    """
    Gera, valida e aplica patches reais no código base.
    Controlado por safety boundaries.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.history_path = self.repo_path / "runtime/patch_history.json"
        self.backup_dir = self.repo_path / "runtime/backups"

        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # SNAPSHOT SYSTEM
    # -----------------------------
    def snapshot(self):
        snapshot = {}

        for file in self.repo_path.rglob("*.py"):
            if "__pycache__" in str(file):
                continue

            snapshot[str(file)] = file.read_text(encoding="utf-8")

        return snapshot

    # -----------------------------
    # BACKUP
    # -----------------------------
    def backup(self):
        snap = self.snapshot()
        h = hashlib.sha256(json.dumps(snap).encode()).hexdigest()

        backup_file = self.backup_dir / f"{h}.json"
        backup_file.write_text(json.dumps(snap, indent=2))

        return str(backup_file)

    # -----------------------------
    # APPLY PATCH (SAFE)
    # -----------------------------
    def apply_patch(self, patch: dict):

        target = self.repo_path / patch["file"]
        new_content = patch["content"]

        if not target.exists():
            raise FileNotFoundError(target)

        old_content = target.read_text(encoding="utf-8")

        diff = difflib.unified_diff(
            old_content.splitlines(),
            new_content.splitlines(),
            fromfile="before",
            tofile="after"
        )

        diff_text = "\n".join(diff)

        # backup before change
        backup_id = self.backup()

        try:
            target.write_text(new_content, encoding="utf-8")

            return {
                "status": "applied",
                "file": patch["file"],
                "backup": backup_id,
                "diff": diff_text
            }

        except Exception as e:

            # rollback
            self.rollback(backup_id)

            return {
                "status": "failed",
                "error": str(e),
                "rolled_back": True
            }

    # -----------------------------
    # ROLLBACK SYSTEM
    # -----------------------------
    def rollback(self, backup_id: str):

        backup_file = Path(backup_id)

        if not backup_file.exists():
            return False

        data = json.loads(backup_file.read_text())

        for file_path, content in data.items():
            Path(file_path).write_text(content, encoding="utf-8")

        return True

    # -----------------------------
    # VALIDATION
    # -----------------------------
    def validate_patch(self, patch: dict) -> bool:

        forbidden = [
            "security",
            "runtime/bootstrap",
            "path_guard"
        ]

        if any(f in patch["file"] for f in forbidden):
            return False

        if len(patch["content"]) < 10:
            return False

        return True
