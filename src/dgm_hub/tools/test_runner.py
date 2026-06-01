from dgm_hub.execution.command_runner import CommandRunner
from dgm_hub.tools.base import Tool


class TestRunnerTool(Tool):
    name = "tests"

    def __init__(self):
        self.runner = CommandRunner()

    def execute(self, command: list[str]):
        return self.runner.run(command)