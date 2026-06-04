from dgm_hub.evolution.genome import PatchGenome


class SwarmToGenomeConverter:

    def convert(self, swarm_result: dict, error: str) -> PatchGenome:

        return PatchGenome(
            patch=swarm_result["patch"],
            error_signature=error,
            metadata={
                "winner": swarm_result.get("winner"),
                "all_agents": swarm_result.get("all", [])
            }
        )
