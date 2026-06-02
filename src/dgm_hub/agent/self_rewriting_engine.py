from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import traceback


@dataclass
class ExecutionTrace:
    tool: str
    args: Dict[str, Any]
    success: bool
    result: Any = None
    error: str = ""
    rewritten: bool = False


class SelfRewritingEngine:
    """
    v3 execution layer:
    - executes plans
    - observes failures
    - rewrites execution strategy
    - retries intelligently
    """

    def __init__(self, runtime, agent):
        self.runtime = runtime
        self.agent = agent
        self.trace: List[ExecutionTrace] = []

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    def run(self, objective: str, max_iterations: int = 5):

        plan = self.agent.plan(objective)

        for i in range(max_iterations):

            tool_name = plan["tool"]
            args = plan.get("args", {})

            try:
                tool = self.runtime.registry.get(tool_name)

                if tool is None:
                    raise Exception(f"Tool not found: {tool_name}")

                # CONTRACT LAYER RESOLUTION
                resolved_args = self.runtime.contract_layer.resolve(tool_name, args)
                result = tool.execute(**resolved_args)

                self.trace.append(
                    ExecutionTrace(
                        tool=tool_name,
                        args=resolved_args,
                        success=True,
                        result=result
                    )
                )

                return {
                    "success": True,
                    "result": result,
                    "trace": self.trace
                }

            except Exception as e:

                error_msg = traceback.format_exc()

                self.trace.append(
                    ExecutionTrace(
                        tool=tool_name,
                        args=args,
                        success=False,
                        error=error_msg
                    )
                )

                # -------------------------
                # REWRITE DECISION
                # -------------------------
                plan = self._rewrite_plan(
                    objective,
                    plan,
                    error_msg
                )

        return {
            "success": False,
            "trace": self.trace
        }

    # -----------------------------
    # CORE REWRITER
    # -----------------------------
    def _rewrite_plan(self, objective, plan, error):

        tool = plan["tool"]

        # SIMPLE HEURISTICS (v3 baseline brain)

        if "missing" in error.lower():
            plan["args"] = plan.get("args", {})
            plan["args"]["repo_path"] = str(self.runtime.root_path)

        elif "not found" in error.lower():
            plan["tool"] = "cmd"
            plan["args"] = {"command": "echo fallback execution"}

        elif "TypeError" in error:
            plan["args"] = {}

        elif "permission" in error.lower():
            plan["tool"] = "audit"
            plan["args"] = {"action": "check_permissions"}

        else:
            plan["tool"] = "cmd"
            plan["args"] = {"command": "echo unknown failure recovery"}

        plan["rewritten"] = True

        return plan
