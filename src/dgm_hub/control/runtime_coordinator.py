from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dgm_hub.runtime.logger import RuntimeLogger


@dataclass
class RuntimeContext:
    session_id: str
    repository_path: Path
    workspace_path: Path


class RuntimeCoordinator:

    def __init__(
        self,
        approval_engine,
        execution_runner,
        validator,
        rollback_manager,
        event_stream,
        logger: RuntimeLogger,
    ):
        self.approval_engine = approval_engine
        self.execution_runner = execution_runner
        self.validator = validator
        self.rollback_manager = rollback_manager
        self.event_stream = event_stream
        self.logger = logger

    def execute(
        self,
        context: RuntimeContext,
        plan: dict[str, Any],
    ):

        self.event_stream.emit(
            "execution_started",
            session=context.session_id,
        )

        approval = self.approval_engine.review(
            context,
            plan,
        )

        if not approval:

            self.event_stream.emit(
                "execution_denied",
                session=context.session_id,
            )

            return {
                "success": False,
                "reason": "approval_denied",
            }

        snapshot = self.rollback_manager.snapshot(
            context.workspace_path,
        )

        try:

            result = self.execution_runner.run(
                context,
                plan,
            )

            validation = self.validator.validate(
                context,
                result,
            )

            if not validation.success:

                self.rollback_manager.restore(
                    snapshot,
                    context.workspace_path,
                )

                return {
                    "success": False,
                    "rollback": True,
                    "validation": validation.reason,
                }

            self.event_stream.emit(
                "execution_completed",
                session=context.session_id,
            )

            return {
                "success": True,
                "result": result,
            }

        except Exception:

            self.rollback_manager.restore(
                snapshot,
                context.workspace_path,
            )

            raise
