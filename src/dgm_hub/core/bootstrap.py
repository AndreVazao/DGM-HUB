from dgm_hub.core.runtime import Runtime
from dgm_hub.security.path_guard import PathGuard
from dgm_hub.tools.filesystem_tool import FilesystemTool
from dgm_hub.tools.powershell_tool import PowerShellTool
from dgm_hub.tools.cmd_tool import CmdTool
from dgm_hub.tools.repo_tool import RepoTool
from dgm_hub.tools.test_runner import TestRunnerTool


def build_runtime(config: dict):
    runtime = Runtime()

    guard = PathGuard(
        config["allowed_paths"]
    )

    runtime.registry.register(
        FilesystemTool(guard)
    )

    runtime.registry.register(
        PowerShellTool()
    )

    runtime.registry.register(
        CmdTool()
    )

    runtime.registry.register(
        RepoTool(guard)
    )

    runtime.registry.register(
        TestRunnerTool()
    )

    return runtime
