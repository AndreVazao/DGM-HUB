from typing import Any
from dgm_hub.agent.self_rewriting_engine import SelfRewritingEngine
from dgm_hub.agent.governor import CognitiveGovernor
from dgm_hub.control.task_graph import TaskGraph
from dgm_hub.memory.execution_memory import ExecutionMemory
from dgm_hub.security.patch_authority import PatchAuthority
from dgm_hub.agent.evolution_orchestrator import EvolutionOrchestrator
from dgm_hub.agent.active_patch_engine import ActivePatchEngine
from dgm_hub.agent.evolution_to_patch import EvolutionToPatch
from dgm_hub.swarm.agent_node import SwarmAgent
from dgm_hub.swarm.swarm_coordinator import SwarmCoordinator
from dgm_hub.swarm.debate_engine import DebateEngine
from dgm_hub.swarm.voting_system import VotingSystem


class AgentEngine:

    def __init__(self, runtime):
        self.runtime = runtime
        self.rewriter = SelfRewritingEngine(runtime, self)

        # Civilization Core
        self.governor = CognitiveGovernor(policy={
            "blocked_keywords": ["rm -rf", "delete system", "format"]
        })
        self.task_graph = TaskGraph()
        self.memory = ExecutionMemory()

        # Patch Authority & Evolution
        self.patch_authority = PatchAuthority(mode="REVIEW")
        self.patch_engine = ActivePatchEngine(repo_path=str(runtime.root_path))
        self.evolution = EvolutionOrchestrator(
            memory=self.memory,
            patch_authority=self.patch_authority
        )
        self.converter = EvolutionToPatch()

        # Swarm Layer
        agents = [
            SwarmAgent("A1", "architect", self),
            SwarmAgent("A2", "optimizer", self),
            SwarmAgent("A3", "debugger", self),
            SwarmAgent("A4", "implementer", self)
        ]
        self.swarm = SwarmCoordinator(
            agents=agents,
            voting_system=VotingSystem(),
            debate_engine=DebateEngine()
        )

    def run(self, objective: str):
        """
        v4 execution entry: Civilization Loop
        """
        # 1. Governor Evaluation
        decision = self.governor.evaluate(objective)
        if not decision.allowed:
            return {"status": "rejected", "reason": decision.reason}

        # 2. Task Graph Entry
        task_id = self.task_graph.create_task(objective)

        # 3. Swarm Execution
        swarm_result = self.swarm.execute_task(objective)

        # 4. Result Processing
        winner = swarm_result.get("winner")
        final_result = None

        if winner and winner.get("proposal"):
            # Use rewriter for actual execution of the chosen proposal
            final_result = self.rewriter.run(winner["proposal"])
        else:
            # Fallback to basic execution if no consensus/winner
            final_result = self.rewriter.run(objective)

        # 5. Task Graph Update
        self.task_graph.update(task_id, status="completed", result=final_result)

        # 6. Memory Logging
        log_entry = {
            "objective": objective,
            "success": final_result.get("success", False) if isinstance(final_result, dict) else True,
            "result": final_result
        }
        self.memory.log(log_entry)

        # 7. Evolution Cycle
        evolution_report = self.evolution.run()
        self.evolution_cycle(evolution_report)

        return final_result

    def evolution_cycle(self, evolution_report):
        for proposal in evolution_report.get("approved_patches", []):
            patch = self.converter.convert(proposal)
            if not patch:
                continue
            if not self.patch_authority.approve(patch):
                continue
            result = self.patch_engine.apply_patch(patch)
            print(f"[EVOLUTION] Patch applied: {patch['file']} - Result: {result['status']}")

    # -----------------------------
    # PLANNER (Required by Rewriter)
    # -----------------------------
    def plan(self, objective: str) -> dict:
        """
        Simple heuristic planner for the execution loop
        """
        text = objective.lower()

        if "git" in text:
            return {
                "tool": "git",
                "args": {"operation": "status"}
            }

        if "files" in text or "tree" in text:
            return {
                "tool": "repo",
                "args": {"operation": "tree"}
            }

        return {
            "tool": "cmd",
            "args": {"command": f"echo execution objective: {objective}"}
        }
