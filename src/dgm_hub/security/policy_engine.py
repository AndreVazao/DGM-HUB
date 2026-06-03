class PolicyEngine:
    def __init__(self):
        self.blocked_paths = [
            ".git",
            "__pycache__",
            ".env",
            "secrets",
            "credentials"
        ]

    def validate_path(self, path: str) -> bool:
        for blocked in self.blocked_paths:
            if blocked in path:
                return False
        return True

    def validate_tool(self, tool_name: str) -> bool:
        allowed = [
            "filesystem_tool",
            "repo_tool",
            "cmd_tool",
            "test_runner",
            "git_tool",
            "powershell_tool",
            "filesystem_guard"
        ]
        return tool_name in allowed
