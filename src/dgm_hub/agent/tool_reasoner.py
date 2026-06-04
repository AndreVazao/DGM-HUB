from typing import Any


class ToolReasoner:

    def __init__(self):

        pass

    def decide_tools(
        self,
        repository_context: dict
    ) -> list:

        """
        Decides which tools should be used based on repo state.
        """

        files = repository_context.get("files", [])
        directories = repository_context.get("directories", [])
        root = repository_context.get("root", ".")

        tool_calls = []

        # heuristic v1 (simple but functional)

        if ".git" in directories:

            tool_calls.append({
                "name": "git_tool",
                "payload": {
                    "operation": "status",
                    "repo_path": root
                }
            })

        if len(files) > 10 or len(directories) > 5:

            tool_calls.append({
                "name": "repo_tool",
                "payload": {
                    "operation": "summary",
                    "repo_path": root
                }
            })

        return tool_calls
