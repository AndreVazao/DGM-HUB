from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.memory.execution_journal import ExecutionJournal


class EngineeringLoop:

    def __init__(self, journal=None):
        self.engine = ExecutionEngine()
        self.journal = journal or ExecutionJournal()

    def run(self, plan, max_iterations=3):
        iteration = 0
        last_result = None

        while iteration < max_iterations:
            print(f"\n[ENGINE LOOP] Iteration {iteration}")
            result = self.engine.execute(plan, journal=self.journal)
            last_result = result

            if self._is_success(result):
                print("[ENGINE LOOP] SUCCESS")
                return {"status": "success", "result": result, "iterations": iteration + 1}

            print("[ENGINE LOOP] FAILURE -> REPLANNING")
            plan = self._replan(plan, result)
            iteration += 1

        return {"status": "failed", "last_result": last_result, "iterations": iteration}

    def _is_success(self, result):
        return all(r["status"] == "ok" for r in result)

    def _replan(self, plan, result):
        # Initial version: simple retry logic
        # In the future, this can be integrated with LLM for smarter replanning
        failed_actions = [r for r in result if r["status"] == "error"]
        plan.summary += f" | retry failed actions (iteration failed with {len(failed_actions)} errors)"
        return plan
