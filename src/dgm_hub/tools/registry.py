from typing import Any

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Any] = {}

    def register(self, name: str | Any, tool: Any | None = None):
        if tool is None:
            tool = name
            name = getattr(tool, "name", tool.__class__.__name__)

        self._tools[name] = tool

        for alias in getattr(tool, "aliases", []):
            self._tools[alias] = tool

    def get(self, name: str):
        return self._tools.get(name)

    def list_tools(self):
        return list(self._tools.keys())
