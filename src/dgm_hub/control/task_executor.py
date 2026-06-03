from dataclasses import dataclass
from typing import Any

from dgm_hub.execution.execution_history import ExecutionHistory
from dgm_hub.execution.repository_context import RepositoryContextGenerator
from dgm_hub.control.workflow_runtime import WorkflowRuntime
from dgm_hub.tools.unified_tool_manager import UnifiedToolManager


@dataclass
class TaskExecutionResult:

    success: bool
    repository_context: dict | None = None
    tool_results: list | None = None
    test_result: Any = None
    error: str | None = None


class TaskExecutor:

    def __init__(self):

        self.runtime = WorkflowRuntime()

        self.history = ExecutionHistory()

        self.repository = RepositoryContextGenerator()

        self.tools = UnifiedToolManager()

    def execute(
        self,
        repository_path: str,
        test_command: str | None = None,
        tool_calls: list | None = None
    ):

        try:

            context = self.repository.build(repository_path)

            tool_results = []

            if tool_calls:

                for call in tool_calls:

                    result = self.tools.execute(
                        call["name"],
                        call.get("payload", {})
                    )

                    tool_results.append({
                        "tool": call["name"],
                        "result": result
                    })

            if test_command:

                test_result = self.runtime.run_tests(test_command)

            else:

                test_result = None

            self.history.add(
                "task_execute",
                True
            )

            return TaskExecutionResult(
                success=True,
                repository_context=context,
                tool_results=tool_results,
                test_result=test_result
            )

        except Exception as exc:

            self.history.add(
                "task_execute",
                False
            )

            return TaskExecutionResult(
                success=False,
                error=str(exc)
            )
