from dgm_hub.control.runtime_session import RuntimeSession
from dgm_hub.security.policy_engine import PolicyEngine
from dgm_hub.mcp.protocol import MCPRequest, MCPResponse

class MCPRouter:
    def __init__(self):
        self.runtime = RuntimeSession()
        self.policy = PolicyEngine()

    def dispatch(self, request: MCPRequest) -> MCPResponse:
        try:
            if not self.policy.validate_tool(request.tool):
                return MCPResponse(
                    success=False,
                    error="Tool blocked by policy"
                )

            result = self.runtime.executor.tools.execute(
                request.tool,
                request.payload
            )

            return MCPResponse(
                success=True,
                result=result
            )

        except Exception as exc:
            return MCPResponse(
                success=False,
                error=str(exc)
            )
