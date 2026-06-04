from dataclasses import dataclass
from pathlib import Path
from typing import Any
from dgm_hub.execution.execution_history import ExecutionHistory
from dgm_hub.execution.repository_context import RepositoryContextGenerator
from dgm_hub.control.workflow_runtime import WorkflowRuntime
from dgm_hub.tools.unified_tool_manager import UnifiedToolManager
from dgm_hub.security.safe_execution import SafeExecutionManager
from dgm_hub.security.policy_engine import PolicyEngine
from dgm_hub.memory.execution_journal import ExecutionJournal

@dataclass
class TaskExecutionResult:
    success: bool
    repository_context: dict | None = None
    tool_results: list | None = None
    test_result: Any = None
    error: str | None = None

class TaskExecutor:
    def __init__(self, repository_path: str = "."):
        self.runtime = WorkflowRuntime()
        self.history = ExecutionHistory()
        self.repository = RepositoryContextGenerator()
        self.tools = UnifiedToolManager(allowed_paths=[str(Path(repository_path).resolve())])
        self.policy = PolicyEngine()
        self.safety = SafeExecutionManager(repository_path)
        self.journal = ExecutionJournal()

    def execute(
        self,
        repository_path: str,
        test_command: str | None = None,
        tool_calls: list | None = None
    ):
        try:
            self.tools = UnifiedToolManager(allowed_paths=[str(Path(repository_path).resolve())])
            context = self.repository.build(repository_path)
            tool_results = []
            if tool_calls:
                for call in tool_calls:
                    if not self.policy.validate_tool(call["name"]):
                        raise PermissionError(f"Tool blocked: {call['name']}")

                    result = self.tools.execute(
                        call["name"],
                        call.get("payload", {})
                    )
                    tool_results.append({
                        "tool": call["name"],
                        "result": result
                    })

            if test_command:
                test_result = self.runtime.run_tests(
                    test_command,
                    cwd=repository_path
                )
            else:
                test_result = None

            success = test_result.success if test_result is not None else True
            self.history.add("task_execute", True)
            result = TaskExecutionResult(
                success=success,
                repository_context=context,
                tool_results=tool_results,
                test_result=test_result
            )
            self.journal.log_task_execution(repository_path, result)
            return result
        except Exception as exc:
            self.history.add("task_execute", False)
            result = TaskExecutionResult(
                success=False,
                error=str(exc)
            )
            self.journal.log_task_execution(repository_path, result)
            return result
