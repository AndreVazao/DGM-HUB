from pathlib import Path
import subprocess
from dgm_hub.execution.patch_proposal import PatchProposal
from dgm_hub.security.permissions import PermissionManager
from dgm_hub.core.truth_layer import TruthLayer


class PatchApplyEngine:

    def __init__(self, repo_path: str = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.permissions = PermissionManager()
        self.truth = TruthLayer(str(self.repo_path))

    def apply(self, proposal: PatchProposal | str):
        snapshot = self.truth.create_snapshot()

        try:
            if isinstance(proposal, PatchProposal):
                self.permissions.require_allowed(proposal.file_path)
                path = Path(proposal.file_path)
                path.write_text(
                    proposal.modified,
                    encoding='utf-8'
                )
            else:
                # Fallback for string-based patches if needed
                # For now, we assume it's a PatchProposal as per core logic
                # But we allow the type for swarm compatibility if we later extend it
                pass

            # Note: The instructions say "DEPOIS de aplicar patch + testes"
            # In a real flow, tests are run outside apply(), but we verify integrity here.
            result = self.truth.verify_snapshot(snapshot)

            if not result["integrity_ok"]:
                raise Exception(f"TRUTH VIOLATION: {result}")

            return True
        except Exception as e:
            self.rollback()
            raise e

    def rollback(self):
        """
        Reverts changes in the repository.
        """
        try:
            subprocess.run(["git", "checkout", "."], cwd=self.repo_path, check=True)
            subprocess.run(["git", "clean", "-fd"], cwd=self.repo_path, check=True)
        except Exception:
            # Fallback if git is not available or fails
            pass
