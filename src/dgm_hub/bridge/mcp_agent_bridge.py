import requests

class MCPAgentBridge:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def run_tool(self, tool: str, payload: dict):
        return requests.post(
            f"{self.base_url}/mcp",
            json={
                "tool": tool,
                "payload": payload,
                "session_id": "local"
            }
        ).json()

    def run_task(self, repo: str, test: str):
        return self.run_tool(
            "agent_loop",
            {
                "repository_path": repo,
                "test_command": test
            }
        )
