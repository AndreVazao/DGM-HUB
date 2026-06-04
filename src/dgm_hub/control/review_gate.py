class ReviewGate:
    def requires_human_approval(self, patch_result) -> bool:
        if not patch_result:
            return False
        if isinstance(patch_result, dict):
            return patch_result.get("status") == "pending"
        return False
