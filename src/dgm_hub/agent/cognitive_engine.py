from dataclasses import dataclass, field
from pathlib import Path
import traceback
from dgm_hub.evolution.evolution_engine import EvolutionEngine


@dataclass
class CognitiveState:
    objective: str
    success: bool = False
    steps: list = field(default_factory=list)
    memory: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    fixes: int = 0


class CognitiveAgent:

    def __init__(self, runtime):
        self.runtime = runtime
        self.repo_root = str(Path.cwd())
        self.evolution = EvolutionEngine()

    # ---------------------------------
    # MAIN LOOP
    # ---------------------------------
    def run(self, objective: str, max_iterations=6):

        state = CognitiveState(objective=objective)
        plan = None

        for iteration in range(max_iterations):

            try:
                if plan is None:
                    plan = self._plan(objective, state)

                result = self._execute(plan)

                state.steps.append({
                    "iteration": iteration,
                    "plan": plan,
                    "result": result
                })

                state.success = True

                self.evolution.learn(
                    objective,
                    plan,
                    True,
                    result
                )

                return state

            except Exception as e:
                err = traceback.format_exc()
                state.steps.append({
                    "iteration": iteration,
                    "plan": plan,
                    "error": err
                })
                state.fixes += 1

                self.evolution.learn(
                    objective,
                    plan,
                    False,
                    {
                        "error": str(e)
                    }
                )

                plan = self.evolution.evolve_plan(
                    plan,
                    True
                )

        return state

    # ---------------------------------
    # PLANNER
    # ---------------------------------
    def _plan(self, objective, state):
        text = objective.lower()

        if "git" in text:
            return {
                "tool": "git",
                "operation": "status"
            }

        if "repo" in text or "inspect" in text:
            return {
                "tool": "repo",
                "operation": "tree"
            }

        if "hello" in text:
            return {
                "tool": "cmd",
                "command": "echo hello"
            }

        return {
            "tool": "git",
            "operation": "status"
        }

    # ---------------------------------
    # EXECUTOR
    # ---------------------------------
    def _execute(self, plan):
        tool_name = plan["tool"]
        plan_args = {k: v for k, v in plan.items() if k != "tool"}

        # CONTRACT LAYER RESOLUTION (MANDATORY PATCH)
        args = self.runtime.contract_layer.resolve(tool_name, plan_args)

        tool = self.runtime.registry.get(tool_name)

        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")

        return tool.execute(**args)
