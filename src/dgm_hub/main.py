from pathlib import Path

from dgm_hub.core.config import ConfigLoader
from dgm_hub.core.bootstrap import build_runtime

from dgm_hub.mcp.server import MCPServer

from dgm_hub.agent.autonomous_dev import AutonomousDevEngine


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
    # FULL AUTONOMOUS DEV LOOP
    # -----------------------------
    engine = AutonomousDevEngine(runtime)

    state = engine.run("git status check")

    print("\n==============================")
    print("FULL AUTONOMOUS DEV RESULT")
    print("==============================")
    print("SUCCESS:", state.success)
    print("ERROR:", state.last_error)
    print("FIXES:", state.fixes)
    print("CYCLES:", len(state.history))

    print("\n--- TRACE ---")
    for h in state.history:
        print(h)


if __name__ == "__main__":
    main()
