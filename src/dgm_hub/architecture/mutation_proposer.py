from dgm_hub.architecture.architecture_graph import ArchitectureGraph


class ArchitectureMutationProposer:

    def propose(self, graph: ArchitectureGraph, analysis: dict):

        proposals = []

        if analysis["cycles"]:
            proposals.append({
                "type": "break_cycle",
                "action": "introduce_interface_layer",
                "target": analysis["cycles"]
            })

        if analysis["high_coupling"]:
            proposals.append({
                "type": "refactor_module",
                "action": "split_module",
                "target": analysis["high_coupling"]
            })

        if analysis["risk_score"] > 5:
            proposals.append({
                "type": "architecture_restructure",
                "action": "introduce_layered_architecture"
            })

        return proposals
