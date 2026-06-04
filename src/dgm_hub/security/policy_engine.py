from pathlib import Path, PurePath


class PolicyEngine:
    def __init__(self):
        self.blocked_path_parts = {
            ".git",
            "__pycache__",
            ".env",
            "secrets",
            "credentials",
        }
        self.allowed_tools = {
            "filesystem_tool",
            "repo_tool",
            "cmd_tool",
            "test_runner",
            "git_tool",
            "powershell_tool",
            "filesystem_guard",
        }
        self.blocked_command_terms = {
            " del ",
            " erase ",
            " format ",
            " reboot",
            " reset --hard",
            " rmdir ",
            " rm ",
            " shutdown",
        }

    def validate_path(self, path: str) -> bool:
        parts = {part.lower() for part in PurePath(path).parts}
        return not parts.intersection(self.blocked_path_parts)

    def validate_path_within(self, path: str, base_dir: str | Path) -> bool:
        if not self.validate_path(path):
            return False

        base = Path(base_dir).resolve()
        target = (base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()

        try:
            target.relative_to(base)
            return True
        except ValueError:
            return False

    def validate_command(self, command: str) -> bool:
        lowered = f" {command.lower()} "
        return not any(term in lowered for term in self.blocked_command_terms)

    def validate_tool(self, tool_name: str) -> bool:
        return tool_name in self.allowed_tools
