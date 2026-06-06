import sys
from dgm_hub.execution.command_runner import CommandRunner
from dgm_hub.tools.base import Tool


class PowerShellTool(Tool):
    name = "powershell_tool"
    aliases = ["powershell"]

    def __init__(self):
        self.runner = CommandRunner()

    def execute(self, command: str):
        if sys.platform == "win32":
            return self.runner.run([
                "powershell",
                "-NoProfile",
                "-Command",
                command,
            ])
        else:
            return self.runner.run([
                "bash",
                "-c",
                command,
            ])
