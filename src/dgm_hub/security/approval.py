class ApprovalEngine:

    def requires_approval(self, proposal_or_action: any) -> bool:

        # Handle both string actions and PatchProposalResult objects
        if hasattr(proposal_or_action, "original") and hasattr(proposal_or_action, "modified"):
            return proposal_or_action.original != proposal_or_action.modified

        dangerous = [
            "delete",
            "remove",
            "reset",
            "format",
            "shutdown",
            "reboot",
        ]

        lowered = str(proposal_or_action).lower()

        return any(x in lowered for x in dangerous)
