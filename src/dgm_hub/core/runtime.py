from dgm_hub.tools.registry import ToolRegistry
from dgm_hub.tools.manager import ToolManager


class Runtime:
    def __init__(self):
        self.registry = ToolRegistry()
        self.tools = ToolManager(self.registry)

    def start(self):
        print("DGM-HUB runtime initialized")
