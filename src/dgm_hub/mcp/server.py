from fastapi import FastAPI
from dgm_hub.mcp.router import MCPRouter
from dgm_hub.mcp.protocol import MCPRequest, MCPResponse

app = FastAPI(title="DGM-HUB MCP")
router = MCPRouter()

@app.post("/mcp")
def run_mcp(request: MCPRequest) -> MCPResponse:
    return router.dispatch(request)

@app.get("/health")
def health():
    return {"status": "ok"}
