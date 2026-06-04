from dgm_hub.architecture.architecture_graph import ArchitectureGraph


class DriftDetector:

    def analyze(self, graph: ArchitectureGraph) -> dict:
        cycles = graph.find_cycles()

        high_coupling = [
            n for n in graph.nodes.values()
            if len(n.dependencies) > 6
        ]

        return {
            "cycles": cycles,
            "high_coupling": [n.name for n in high_coupling],
            "risk_score": len(cycles) * 2 + len(high_coupling)
        }
