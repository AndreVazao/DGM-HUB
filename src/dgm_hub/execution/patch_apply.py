from pathlib import Path
from dgm_hub.execution.patch_proposal import PatchProposal
from dgm_hub.security.permissions import PermissionManager


class PatchApplyEngine:

    def __init__(self):
        self.permissions = PermissionManager()

    def apply(self, proposal: PatchProposal):

        self.permissions.require_allowed(proposal.file_path)

        path = Path(proposal.file_path)

        path.write_text(
            proposal.modified,
            encoding='utf-8'
        )

        return True
