from dgm_hub.agent.evolution_loop import EvolutionLoop
from dgm_hub.security.evolution_guard import EvolutionGuard


class EvolutionOrchestrator:

    def __init__(self, memory, patch_authority):
        self.loop = EvolutionLoop()
        self.guard = EvolutionGuard(patch_authority)
        self.memory = memory

    # -------------------------
    # RUN FULL EVOLUTION CYCLE
    # -------------------------
    def run(self):

        analysis = self.loop.analyze()
        issues = self.loop.detect_issues()
        patches = self.loop.propose_patches(issues)

        approved = []

        for patch in patches:
            if self.guard.validate(patch):
                approved.append(patch)

        return {
            "analysis": analysis,
            "issues": issues,
            "approved_patches": approved
        }
