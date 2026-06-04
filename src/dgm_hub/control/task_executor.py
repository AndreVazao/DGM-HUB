from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
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
        self.repository_path = Path(repository_path).resolve()
        self.runtime = WorkflowRuntime()
        self.history = ExecutionHistory()
        self.repository = RepositoryContextGenerator()
        self.tools = UnifiedToolManager(allowed_paths=[str(self.repository_path)])
        self.policy = PolicyEngine()
        self.safety = SafeExecutionManager(str(self.repository_path))

        repo_hash = hashlib.md5(str(self.repository_path).encode()).hexdigest()[:8]
        journal_path = Path("runtime/journals") / f"{self.repository_path.name}_{repo_hash}.jsonl"
        self.journal = ExecutionJournal(path=journal_path)

    def execute(
        self,
        repository_path: str,
        test_command: str | None = None,
        tool_calls: list | None = None
    ):
        snapshot = None
        try:
            repo_p = Path(repository_path).resolve()
            if repo_p != self.repository_path:
                self.tools = UnifiedToolManager(allowed_paths=[str(repo_p)])
                repo_hash = hashlib.md5(str(repo_p).encode()).hexdigest()[:8]
                journal_path = Path("runtime/journals") / f"{repo_p.name}_{repo_hash}.jsonl"
                self.journal = ExecutionJournal(path=journal_path)
                self.safety = SafeExecutionManager(str(repo_p))

            snapshot = self.safety.create_snapshot(str(repo_p))
            context = self.repository.build(str(repo_p))
            tool_results = []
            if tool_calls:
                for call in tool_calls:
                    if not self.policy.validate_tool(call["name"]):
                        raise PermissionError(f"Tool blocked: {call['name']}")
                    result = self.tools.execute(call["name"], call.get("payload", {}))
                    tool_results.append({"tool": call["name"], "result": result})

            if test_command:
                test_result = self.runtime.run_tests(test_command, cwd=str(repo_p))
            else:
                test_result = None

            success = test_result.success if test_result is not None else True
            if snapshot:
                self.safety.rollback(snapshot)

            self.history.add("task_execute", True)
            result = TaskExecutionResult(
                success=success,
                repository_context=context,
                tool_results=tool_results,
                test_result=test_result
            )
            self.journal.log_task_execution(str(repo_p), result)
            return result
        except Exception as exc:
            if snapshot:
                try: self.safety.rollback(snapshot)
                except: pass
            self.history.add("task_execute", False)
            result = TaskExecutionResult(success=False, error=str(exc))
            self.journal.log_task_execution(repository_path, result)
            return result
