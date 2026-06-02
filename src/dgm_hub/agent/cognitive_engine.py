from dataclasses import dataclass, field
from pathlib import Path
import traceback


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

        self.repo_root = str(
            Path.cwd()
        )

    # ---------------------------------
    # MAIN LOOP
    # ---------------------------------

    def run(
        self,
        objective:str,
        max_iterations=6
    ):

        state = CognitiveState(
            objective=objective
        )

        for iteration in range(
            max_iterations
        ):

            try:

                plan = self._plan(
                    objective,
                    state
                )

                result = self._execute(
                    plan
                )

                state.steps.append({

                    "iteration":iteration,

                    "plan":plan,

                    "result":result

                })

                state.success=True

                return state

            except Exception:

                err = traceback.format_exc()

                state.steps.append({

                    "iteration":iteration,

                    "plan":plan,

                    "error":err

                })

                state.fixes += 1

        return state


    # ---------------------------------
    # PLANNER
    # ---------------------------------

    def _plan(
        self,
        objective,
        state
    ):

        text = objective.lower()

        repo_args = {

            "repo_path":
            self.repo_root

        }

        if "git" in text:

            return {

                "tool":"git",

                "operation":"status",

                **repo_args

            }

        if "repo" in text:

            return {

                "tool":"repo",

                "operation":"tree",

                **repo_args

            }

        if "inspect" in text:

            return {

                "tool":"repo",

                "operation":"tree",

                **repo_args

            }

        if "hello" in text:

            return {

                "tool":"cmd",

                "command":"echo hello"

            }

        return {

            "tool":"git",

            "operation":"status",

            **repo_args

        }


    # ---------------------------------
    # EXECUTOR
    # ---------------------------------

    def _execute(
        self,
        plan
    ):

        tool_name = plan["tool"]

        args = dict(plan)

        del args["tool"]

        tool = self.runtime.registry.get(
            tool_name
        )

        if tool is None:

            raise ValueError(
                f"Tool not found: {tool_name}"
            )

        return tool.execute(
            **args
        )
