from pathlib import Path
from dgm_hub.tools.registry import ToolRegistry
from dgm_hub.tools.manager import ToolManager
from dgm_hub.control.tool_contract_layer import ToolContractLayer


class Runtime:
    def __init__(self):
        self.root_path = Path.cwd()
        self.registry = ToolRegistry()
        self.tools = ToolManager(self.registry)
        self.contract_layer = ToolContractLayer(default_repo=str(self.root_path))

    def start(self):
        print("DGM-HUB runtime initialized")
