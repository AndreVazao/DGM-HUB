from pathlib import Path

from dgm_hub.core.config import ConfigLoader
from dgm_hub.core.bootstrap import build_runtime

# from dgm_hub.mcp.server import MCPServer

from dgm_hub.agent.cognitive_engine import CognitiveAgent


def main():

    config = ConfigLoader(
        str(Path("config/default_config.yaml"))
    ).load()

    runtime = build_runtime(config)
    runtime.start()

    # server = MCPServer(runtime)
    # server.start()

    agent = CognitiveAgent(runtime)

    result = agent.run("audit git repo and fix issues automatically")

    print("\n====================")
    print("COGNITIVE RESULT")
    print("====================")

    print("SUCCESS:", result.success)
    print("FIXES:", result.fixes)

    for s in result.steps:
        print(s)


if __name__ == "__main__":
    main()
