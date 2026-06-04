from dataclasses import dataclass
from pathlib import Path
import traceback
import time

from dgm_hub.core.truth_layer import TruthLayer
from dgm_hub.execution.patch_apply import PatchApplyEngine
from dgm_hub.execution.patch_proposal import PatchProposal
from dgm_hub.execution.test_pipeline import TestPipeline


@dataclass
class FixState:
    repo_path: str
    last_error: str | None = None
    iteration: int = 0
    success: bool = False


class AutonomousFixLoop:
    """
    Closed-loop autonomous repair system:

    detect -> analyze -> patch -> apply -> validate -> commit OR rollback
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

        self.truth = TruthLayer(str(repo_path))
        self.patcher = PatchApplyEngine(str(self.repo_path))
        self.tester = TestPipeline()

    # --------------------------
    # MAIN LOOP
    # --------------------------

    def run(self, max_iterations: int = 5) -> FixState:

        state = FixState(repo_path=str(self.repo_path))

        for i in range(max_iterations):
            state.iteration = i

            print(f"[FIX LOOP] iteration={i}")

            try:
                snapshot = self.truth.create_snapshot()

                # 1. run tests first (detect failure)
                test_result = self.tester.run(self.repo_path)

                if test_result.passed:
                    state.success = True
                    return state

                # 2. analyze error
                error = self._extract_error(test_result)
                state.last_error = error

                # 3. generate patch proposal
                proposal = self._create_patch(error)

                # 4. apply patch
                self.patcher.apply(proposal)

                # 5. verify truth
                result = self.truth.verify_snapshot(snapshot)

                if not result["integrity_ok"]:
                    print("[TRUTH] violation detected → rollback")
                    self.patcher.rollback()
                    continue

                # 6. re-run tests
                test_result = self.tester.run(self.repo_path)

                if test_result.passed:
                    state.success = True
                    return state

                # continue loop if still failing

            except Exception as e:
                print("[FIX LOOP ERROR]", str(e))
                print(traceback.format_exc())

                self.patcher.rollback()
                state.last_error = str(e)

            time.sleep(0.2)

        return state

    # --------------------------
    # PATCH LOGIC
    # --------------------------

    def _create_patch(self, error: str) -> PatchProposal:
        """
        Minimal deterministic repair strategy placeholder.
        (Later: LLM planner can replace this)
        """

        return PatchProposal(
            file_path="placeholder.py",
            original="",
            modified="# placeholder patch - to be replaced by planner",
            reason=f"Auto-fix based on error: {error}"
        )

    def _extract_error(self, test_result) -> str:
        if hasattr(test_result, "stderr") and test_result.stderr:
            return test_result.stderr

        if hasattr(test_result, "output"):
            return str(test_result.output)

        return "unknown error"
