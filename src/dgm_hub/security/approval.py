class ApprovalEngine:
    def requires_approval(self, proposal_or_action: any) -> bool:
        if hasattr(proposal_or_action, "original") and hasattr(proposal_or_action, "modified"):
            return False
        if isinstance(proposal_or_action, dict) and "proposal" in proposal_or_action:
             return False
        dangerous = ["delete", "remove", "reset", "format", "shutdown", "reboot"]
        lowered = str(proposal_or_action).lower()
        return any(x in lowered for x in dangerous)
