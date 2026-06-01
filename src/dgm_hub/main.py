from pathlib import Path

from dgm_hub.core.config import ConfigLoader
from dgm_hub.core.bootstrap import build_runtime
from dgm_hub.mcp.server import MCPServer


def main():

    config_path = Path("config/default_config.yaml")

    config = ConfigLoader(
        str(config_path)
    ).load()

    runtime = build_runtime(
        config
    )

    runtime.start()

    server = MCPServer(
        runtime
    )

    server.start()


if __name__ == "__main__":
    main()
