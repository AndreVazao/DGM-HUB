from .registry import ToolRegistry


class ToolManager:

    def __init__(
        self,
        registry: ToolRegistry
    ):

        self.registry = registry

    def execute(
        self,
        tool_name: str,
        **kwargs
    ):

        tool = self.registry.get(
            tool_name
        )

        if tool is None:

            raise ValueError(
                f"Tool not found: {tool_name}"
            )

        return tool.execute(
            **kwargs
        )
