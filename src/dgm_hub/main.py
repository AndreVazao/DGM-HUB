from pathlib import Path

from dgm_hub.core.config import ConfigLoader
from dgm_hub.core.bootstrap import build_runtime

from dgm_hub.mcp.server import MCPServer
from dgm_hub.agent.engine import AgentEngine


def main():

    config_path = Path("config/default_config.yaml")

    config = ConfigLoader(
        str(config_path)
    ).load()

    runtime = build_runtime(config)

    runtime.start()

    server = MCPServer(runtime)
    server.start()

    # -------------------------
    # AGENT LOOP TEST (NEW)
    # -------------------------
    agent = AgentEngine(runtime)

    state = agent.run("git status check")

    print(state)


if __name__ == "__main__":
    main()
