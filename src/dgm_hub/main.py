from pathlib import Path

from dgm_hub.core.config import ConfigLoader
from dgm_hub.core.bootstrap import build_runtime

from dgm_hub.mcp.server import MCPServer

from dgm_hub.agent.architect_mode import ArchitectEngine


def main():

    config_path = Path("config/default_config.yaml")

    config = ConfigLoader(
        str(config_path)
    ).load()

    runtime = build_runtime(config)

    runtime.start()

    server = MCPServer(runtime)
    server.start()

    # -----------------------------
    # ARCHITECT MODE
    # -----------------------------
    architect = ArchitectEngine(runtime)

    state = architect.run("full system audit")

    print("\n==============================")
    print("ARCHITECT MODE RESULT")
    print("==============================")
    print("SUCCESS:", state.success)
    print("FIXES:", state.fixes)
    print("ERRORS:", len(state.errors))

    print("\nPLAN:")
    print(state.plan)

    print("\nHISTORY:")
    for h in state.history:
        print(h)


if __name__ == "__main__":
    main()
