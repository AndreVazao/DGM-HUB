import sys
from dgm_hub.execution.command_runner import CommandRunner
from dgm_hub.tools.base import Tool


class CmdTool(Tool):
    name = "cmd_tool"
    aliases = ["cmd"]

    def __init__(self):
        self.runner = CommandRunner()

    def execute(self, command: str):
        if sys.platform == "win32":
            return self.runner.run([
                "cmd",
                "/c",
                command,
            ])
        else:
            return self.runner.run([
                "sh",
                "-c",
                command,
            ])
