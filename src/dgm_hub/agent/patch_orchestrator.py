from dgm_hub.execution.patch_apply import PatchApplyEngine
from dgm_hub.security.approval import ApprovalEngine
from dgm_hub.agent.patch_intelligence import PatchIntelligenceEngine


class PatchOrchestrator:

    def __init__(self):

        self.generator = PatchIntelligenceEngine()

        self.approval = ApprovalEngine()

        self.applier = PatchApplyEngine()

    def execute_fix(
        self,
        file_path: str,
        original_code: str,
        error: str,
        line: int | None = None
    ):

        proposal = self.generator.propose_patch(
            file_path=file_path,
            original_code=original_code,
            error=error,
            line=line
        )

        if self.approval.requires_approval(proposal):

            return {
                "status": "pending",
                "proposal": proposal
            }

        self.applier.apply(proposal)

        return {
            "status": "applied",
            "proposal": proposal
        }
