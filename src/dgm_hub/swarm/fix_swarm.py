from dataclasses import dataclass
from typing import List
import random

from dgm_hub.execution.patch_apply import PatchApplyEngine
from dgm_hub.execution.test_pipeline import TestPipeline
from dgm_hub.swarm.fix_agents import LogicAgent, SafetyAgent, AggressiveAgent
from dgm_hub.swarm.voting_system import VotingSystem
from dgm_hub.core.truth_layer import TruthLayer


@dataclass
class SwarmFixResult:
    success: bool
    chosen_patch: str | None
    votes: dict


class FixSwarmEngine:
    """
    Multi-agent bug fixing system with consensus voting.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

        self.tester = TestPipeline()
        self.patcher = PatchApplyEngine(repo_path)
        self.truth = TruthLayer(repo_path)

        self.agents = [
            LogicAgent(),
            SafetyAgent(),
            AggressiveAgent()
        ]

        self.voter = VotingSystem()

    def fix(self, error: str, max_rounds: int = 3) -> SwarmFixResult:

        for round_id in range(max_rounds):

            print(f"[SWARM] round={round_id}")

            patches = []

            # 1. collect proposals
            for agent in self.agents:
                patch = agent.propose_fix(error)
                patches.append(patch)

            # 2. voting
            decision = self.voter.select_best(patches)

            # 3. apply
            self.patcher.apply(decision["patch"])

            # 4. validate truth
            snapshot = self.truth.create_snapshot()
            result = self.truth.verify_snapshot(snapshot)

            if not result["integrity_ok"]:
                print("[SWARM] truth violation → rollback")
                self.patcher.rollback()
                continue

            # 5. test
            test_result = self.tester.run(self.repo_path)

            if test_result.passed:
                return SwarmFixResult(
                    success=True,
                    chosen_patch=decision["patch"],
                    votes=decision
                )

        return SwarmFixResult(
            success=False,
            chosen_patch=None,
            votes={}
        )
