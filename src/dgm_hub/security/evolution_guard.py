class EvolutionGuard:
    """
    Gatekeeper for self-generated evolution patches
    """

    def __init__(self, authority):
        self.authority = authority

    def validate(self, patch: dict) -> bool:

        # block core destructive evolution
        forbidden_targets = [
            "runtime",
            "bootstrap",
            "security",
            "patch_authority"
        ]

        target = patch.get("file", patch.get("target", ""))

        for f in forbidden_targets:
            if f in target:
                return False

        # delegate to authority system
        return self.authority.approve(patch)
