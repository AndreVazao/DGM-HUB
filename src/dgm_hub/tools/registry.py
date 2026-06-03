from typing import Any

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Any] = {}

    def register(self, name: str, tool: Any):
        self._tools[name] = tool

    def get(self, name: str):
        return self._tools.get(name)

    def list_tools(self):
        return list(self._tools.keys())
