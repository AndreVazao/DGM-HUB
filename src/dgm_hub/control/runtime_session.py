from dgm_hub.control.workflow_runtime import WorkflowRuntime
from dgm_hub.execution.execution_history import ExecutionHistory


class RuntimeSession:

    def __init__(self):
        self.runtime = WorkflowRuntime()
        self.history = ExecutionHistory()

    def inspect(self, path:str):

        result = self.runtime.inspect_repository(path)

        self.history.add(
            action='inspect_repository',
            success=True
        )

        return result

    def run_tests(self, command:str):

        result = self.runtime.run_tests(command)

        self.history.add(
            action='run_tests',
            success=result.success
        )

        return result
