from dataclasses import dataclass

from dgm_hub.control.runtime_session import RuntimeSession
from dgm_hub.agent.tool_reasoner import ToolReasoner
from dgm_hub.agent.patch_orchestrator import PatchOrchestrator
from dgm_hub.execution.error_analyzer import ErrorAnalyzer
from dgm_hub.execution.file_loader import FileLoader


@dataclass
class AgentResult:

    success: bool
    context: dict | None = None
    tool_results: list | None = None
    patch_result: any = None
    error: str | None = None


class AgentLoop:

    def __init__(self):

        self.runtime = RuntimeSession()

        self.reasoner = ToolReasoner()

        self.patcher = PatchOrchestrator()

        self.errors = ErrorAnalyzer()

        self.files = FileLoader()

    def run(
        self,
        repository_path: str,
        test_command: str | None = None
    ):

        try:

            execution = self.runtime.execute_task(
                repository_path=repository_path,
                test_command=test_command
            )

            context = execution.repository_context

            tool_calls = self.reasoner.decide_tools(context)

            tool_exec = self.runtime.executor.execute(
                repository_path=repository_path,
                tool_calls=tool_calls
            )

            patch_result = None

            # REAL DEBUG LOOP

            if execution.test_result and hasattr(execution.test_result, "success"):

                if not execution.test_result.success:

                    error = self.errors.parse(
                        str(execution.test_result)
                    )

                    if error.file:

                        code = self.files.read(error.file)

                        patch_result = self.patcher.execute_fix(
                            file_path=error.file,
                            original_code=code,
                            error=error.message,
                            line=error.line
                        )

            return AgentResult(
                success=True,
                context=context,
                tool_results=tool_exec.tool_results,
                patch_result=patch_result
            )

        except Exception as exc:

            return AgentResult(
                success=False,
                error=str(exc)
            )
