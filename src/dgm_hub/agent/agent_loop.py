from dataclasses import dataclass
from dgm_hub.control.runtime_session import RuntimeSession
from dgm_hub.agent.tool_reasoner import ToolReasoner
from dgm_hub.agent.patch_orchestrator import PatchOrchestrator
from dgm_hub.execution.error_analyzer import ErrorAnalyzer
from dgm_hub.execution.file_loader import FileLoader
from dgm_hub.runtime.logger import RuntimeLogger
from dgm_hub.control.review_gate import ReviewGate
from dgm_hub.runtime.telemetry import Telemetry

@dataclass
class AgentResult:
    success: bool
    context: dict | None = None
    tool_results: list | None = None
    test_result: any = None
    patch_result: any = None
    error: str | None = None
    metrics: dict | None = None

class AgentLoop:
    def __init__(self):
        self.runtime = RuntimeSession(repository_path=".")
        self.reasoner = ToolReasoner()
        self.patcher = PatchOrchestrator()
        self.errors = ErrorAnalyzer()
        self.files = FileLoader()
        self.logger = RuntimeLogger()
        self.review_gate = ReviewGate()
        self.telemetry = Telemetry()

    def run(
        self,
        repository_path: str,
        test_command: str | None = None
    ):
        self.logger.log("run_start", {"repo": repository_path})
        self.telemetry.emit("run_start", {"repo": repository_path})
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
            if execution.test_result and hasattr(execution.test_result, "success"):
                if not execution.test_result.success:
                    error = self.errors.parse(str(execution.test_result))
                    if error.file:
                        code = self.files.read(error.file)
                        patch_result = self.patcher.execute_fix(
                            file_path=error.file,
                            original_code=code,
                            error=error.message,
                            line=error.line
                        )

            if self.review_gate.requires_human_approval(patch_result):
                result = AgentResult(
                    success=execution.success,
                    context=context,
                    tool_results=tool_exec.tool_results,
                    test_result=execution.test_result,
                    patch_result={
                        "status": "pending_review",
                        "data": patch_result
                    }
                )
                self.telemetry.emit("run_end", {
                    "success": execution.success,
                    "patch": "pending_review"
                })
                return result

            metrics = {
                "tools_executed": len(tool_exec.tool_results) if tool_exec.tool_results else 0,
                "patch_generated": patch_result is not None
            }

            self.logger.log("run_end", {
                "success": execution.success,
                "patch": patch_result is not None
            })
            self.telemetry.emit("run_end", {
                "success": execution.success,
                "patch": patch_result is not None
            })

            return AgentResult(
                success=execution.success,
                context=context,
                tool_results=tool_exec.tool_results,
                test_result=execution.test_result,
                patch_result=patch_result,
                metrics=metrics
            )
        except Exception as exc:
            self.logger.log("run_end", {
                "success": False,
                "error": str(exc)
            })
            self.telemetry.emit("run_end", {
                "success": False,
                "error": str(exc)
            })
            return AgentResult(
                success=False,
                error=str(exc)
            )
