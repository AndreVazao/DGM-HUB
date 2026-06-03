class ReviewGate:
    def requires_human_approval(self, patch_result) -> bool:
        if not patch_result:
            return False
        # rule v1: always require approval if code changes exist
        return True
