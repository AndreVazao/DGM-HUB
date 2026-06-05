from uuid import uuid4
from pathlib import Path
from dgm_hub.control.task_executor import TaskExecutor, TaskExecutionResult
from dgm_hub.runtime.workspace_manager import WorkspaceManager
from dgm_hub.runtime.events import EventStream
from dgm_hub.control.runtime_coordinator import RuntimeCoordinator, RuntimeContext
from dgm_hub.control.runtime_adapters import (
    ApprovalEngineAdapter,
    ExecutionRunnerAdapter,
    ValidationRunnerAdapter,
    RollbackManagerAdapter
)
from dgm_hub.runtime.live_logger import LOGGER

class RuntimeSession:

    def __init__(self, repository_path: str = "."):
        self.id = str(uuid4())
        self.repository_path = Path(repository_path).resolve()
        self.workspace_manager = WorkspaceManager()
        self.workspace_path = self.workspace_manager.create_workspace(self.repository_path)

        self.event_stream = EventStream()
        self.subscribe_logger()

        # Maintain backward compatibility with TaskExecutor
        # But we also prepare for RuntimeCoordinator
        self.executor = TaskExecutor(repository_path=str(self.workspace_path))

        # Initialize Coordinator
        self.coordinator = RuntimeCoordinator(
            approval_engine=ApprovalEngineAdapter(self.executor.policy),
            execution_runner=ExecutionRunnerAdapter(self.executor.tools, self.executor.runtime),
            validator=ValidationRunnerAdapter(),
            rollback_manager=RollbackManagerAdapter(self.executor.safety),
            event_stream=self.event_stream,
            logger=LOGGER
        )

    def _resolve_path(self, path: str) -> str:
        """Resolves the path to the workspace if it matches the session repository."""
        try:
            p = Path(path).resolve()
            if p == self.repository_path:
                return str(self.workspace_path)
        except Exception:
            pass
        return path

    def inspect(self, path: str):
        return self.executor.execute(
            repository_path=self._resolve_path(path)
        )

    def execute_task(self, repository_path: str, test_command: str | None = None, tool_calls: list | None = None):
        # Use Coordinator for orchestration
        context = RuntimeContext(
            session_id=self.id,
            repository_path=self.repository_path,
            workspace_path=self.workspace_path
        )

        plan = {
            "tool_calls": tool_calls or [],
            "test_command": test_command
        }

        coord_result = self.coordinator.execute(context, plan)

        if coord_result["success"]:
            res = coord_result["result"]
            # Convert to TaskExecutionResult for backward compatibility
            return TaskExecutionResult(
                success=True,
                repository_context=self.executor.repository.build(str(self.workspace_path)),
                tool_results=res.get("tool_results"),
                test_result=res.get("test_result")
            )
        else:
            return TaskExecutionResult(
                success=False,
                error=coord_result.get("reason", coord_result.get("validation", "Execution failed"))
            )

    def close(self):
        self.workspace_manager.cleanup(self.workspace_path)

    def subscribe_logger(self):
        self.event_stream.subscribe(LOGGER)
