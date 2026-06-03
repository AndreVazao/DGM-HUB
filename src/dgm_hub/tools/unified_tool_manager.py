from typing import Any

from dgm_hub.tools.registry import ToolRegistry


class UnifiedToolManager:

    def __init__(self):

        self.registry = ToolRegistry()

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
