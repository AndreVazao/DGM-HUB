class MCPServer:
    def __init__(self, runtime):
        self.runtime = runtime

    def start(self):
        print("DGM-HUB MCP server started")

        while True:
            try:
                input()
            except KeyboardInterrupt:
                break
