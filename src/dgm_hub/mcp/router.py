class MCPRouter:
    def __init__(self, runtime):
        self.runtime = runtime

    def dispatch(self, tool_name: str, payload: dict):
        return self.runtime.tools.execute(
            tool_name,
            **payload,
        )
