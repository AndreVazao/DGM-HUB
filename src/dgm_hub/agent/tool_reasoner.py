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

        tool_calls = []

        # heuristic v1 (simple but functional)

        if any("test" in f.lower() for f in files):

            tool_calls.append({
                "name": "test_runner",
                "payload": {}
            })

        if any(f.endswith(".py") for f in files):

            tool_calls.append({
                "name": "filesystem_tool",
                "payload": {
                    "action": "scan"
                }
            })

        if len(files) > 50:

            tool_calls.append({
                "name": "repo_tool",
                "payload": {
                    "mode": "summary"
                }
            })

        return tool_calls
