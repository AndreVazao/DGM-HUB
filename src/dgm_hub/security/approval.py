class ApprovalEngine:
    def requires_approval(self, action: str) -> bool:
        dangerous = [
            "delete",
            "remove",
            "reset",
            "format",
            "shutdown",
            "reboot",
        ]

        lowered = action.lower()

        return any(x in lowered for x in dangerous)
