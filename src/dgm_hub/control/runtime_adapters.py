from pathlib import Path
from typing import Any
from dgm_hub.security.policy_engine import PolicyEngine
from dgm_hub.security.safe_execution import SafeExecutionManager
from dgm_hub.control.workflow_runtime import WorkflowRuntime
from dgm_hub.tools.unified_tool_manager import UnifiedToolManager

class ApprovalEngineAdapter:
    def __init__(self, policy: PolicyEngine):
        self.policy = policy

    def review(self, context, plan: dict[str, Any]) -> bool:
        # Simple policy check for now
        tool_calls = plan.get("tool_calls", [])
        for call in tool_calls:
            if not self.policy.validate_tool(call["name"]):
                return False
        return True

class ExecutionRunnerAdapter:
    def __init__(self, tools: UnifiedToolManager, runtime: WorkflowRuntime):
        self.tools = tools
        self.runtime = runtime

    def run(self, context, plan: dict[str, Any]) -> dict[str, Any]:
        tool_results = []
        tool_calls = plan.get("tool_calls", [])
        for call in tool_calls:
            result = self.tools.execute(call["name"], call.get("payload", {}))
            tool_results.append({"tool": call["name"], "result": result})

        test_result = None
        test_command = plan.get("test_command")
        if test_command:
            test_result = self.runtime.run_tests(test_command, cwd=str(context.workspace_path))

        return {
            "tool_results": tool_results,
            "test_result": test_result,
            "success": test_result.success if test_result is not None else True
        }

class ValidationRunnerAdapter:
    def validate(self, context, result: dict[str, Any]):
        # Basic validation: check if execution was successful
        success = result.get("success", False)
        return type("Validation", (), {"success": success, "reason": "Execution failed" if not success else None})()

class RollbackManagerAdapter:
    def __init__(self, safety: SafeExecutionManager):
        self.safety = safety

    def snapshot(self, path: Path):
        return self.safety.create_snapshot(str(path))

    def restore(self, snapshot, path: Path):
        if snapshot:
            self.safety.rollback(snapshot)
