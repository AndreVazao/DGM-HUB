from pathlib import Path
from typing import Any, Dict


class ToolContractLayer:
    """
    Normaliza chamadas entre Agent -> Tools
    Resolve:
    - missing repo_path
    - inconsistent tool signatures
    - default injection
    """

    def __init__(self, default_repo: str):
        self.default_repo = default_repo

    def resolve(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:

        args = dict(args)  # clone safe

        # -----------------------------
        # GLOBAL DEFAULTS
        # -----------------------------
        if "repo_path" not in args:
            args["repo_path"] = self.default_repo

        # -----------------------------
        # TOOL-SPECIFIC PATCHES
        # -----------------------------
        if tool_name == "git":

            # normalize operations
            if "operation" not in args:
                args["operation"] = "status"

            # safety fallback
            if args["operation"] not in ["status", "log", "add", "commit", "push"]:
                args["operation"] = "status"

        if tool_name == "repo":

            if "operation" not in args:
                args["operation"] = "tree"

            if "repo_path" not in args:
                args["repo_path"] = self.default_repo

        if tool_name == "cmd":
            if "command" not in args:
                args["command"] = "echo noop"

        return args
