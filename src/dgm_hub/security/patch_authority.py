class PatchAuthority:
    """
    Controls self-modification power
    """

    def __init__(self, mode="REVIEW"):
        self.mode = mode  # DENY | REVIEW | ALLOW

    def approve(self, patch: dict) -> bool:

        target = patch.get("file", patch.get("target", ""))

        # CORE PROTECTION
        blocked = [
            "bootstrap",
            "security",
            "runtime"
        ]

        if any(b in target for b in blocked):
            return False

        if "agent" in target or "cognitive_engine" in target:
            if self.mode != "ALLOW":
                return False

        if self.mode == "DENY":
            return False

        if self.mode == "ALLOW":
            return True

        # REVIEW MODE DEFAULT
        risky_keywords = ["delete", "rewrite", "replace"]

        for k in risky_keywords:
            if k in str(patch).lower():
                return False

        # rule: minimum size for real change
        if "content" in patch and len(patch["content"]) < 50:
            return False

        return True
