from typing import Any

from dgm_hub.security.path_guard import PathGuard
from dgm_hub.tools.cmd_tool import CmdTool
from dgm_hub.tools.filesystem_tool import FilesystemTool
from dgm_hub.tools.git_tool import GitTool
from dgm_hub.tools.powershell_tool import PowerShellTool
from dgm_hub.tools.registry import ToolRegistry
from dgm_hub.tools.repo_tool import RepoTool
from dgm_hub.tools.test_runner import TestRunnerTool


class UnifiedToolManager:

    def __init__(self, allowed_paths: list[str] | None = None):

        self.registry = ToolRegistry()
        self._register_defaults(allowed_paths or ["."])

    def _register_defaults(self, allowed_paths: list[str]):
        guard = PathGuard(allowed_paths)
        self.register_tool(FilesystemTool.name, FilesystemTool(guard))
        self.register_tool(CmdTool.name, CmdTool())
        self.register_tool(PowerShellTool.name, PowerShellTool())
        self.register_tool(RepoTool.name, RepoTool())
        self.register_tool(TestRunnerTool.name, TestRunnerTool())
        self.register_tool(GitTool.name, GitTool(guard))

    def register_tool(self, name: str, tool: Any):

        self.registry.register(name, tool)

    def execute(self, name: str, payload: dict | None = None):

        tool = self.registry.get(name)

        if tool is None:

            raise RuntimeError(f"Tool not found: {name}")

        if payload is None:

            payload = {}

        # unified execution contract
        if hasattr(tool, "execute"):

            return tool.execute(**payload)

        if callable(tool):

            return tool(**payload)

        raise RuntimeError(f"Invalid tool type: {name}")
