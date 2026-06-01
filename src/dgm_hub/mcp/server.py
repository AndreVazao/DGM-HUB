import json

from dgm_hub.mcp.router import MCPRouter


class MCPServer:

    def __init__(self, runtime):

        self.runtime = runtime
        self.router = MCPRouter(runtime)

    def start(self):

        print("DGM-HUB MCP server started")

        while True:

            try:

                raw = input()

                if not raw:
                    continue

                payload = json.loads(raw)

                result = self.router.dispatch(
                    payload["tool"],
                    payload.get("args", {})
                )

                print(
                    json.dumps(
                        result,
                        ensure_ascii=False,
                        default=str
                    )
                )

            except KeyboardInterrupt:
                break

            except Exception as e:

                # NÃO expor stack trace ao utilizador
                print(
                    json.dumps({
                        "error": str(e)
                    })
                )