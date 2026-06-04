import argparse
from pathlib import Path
from local_bootstrap import enable_src_imports

enable_src_imports()

from dgm_hub.core.config import ConfigLoader
from dgm_hub.core.bootstrap import build_runtime

# from dgm_hub.mcp.server import MCPServer

from dgm_hub.agent.cognitive_engine import CognitiveAgent


def main():
    parser = argparse.ArgumentParser(description="Run the local DGM-HUB cognitive agent.")
    parser.add_argument(
        "objective",
        nargs="?",
        default="audit git repo and fix issues automatically",
        help="Objective for the cognitive agent.",
    )
    parser.add_argument("--config", default="config/default_config.yaml")
    args = parser.parse_args()

    config = ConfigLoader(
        str(Path(args.config))
    ).load()

    runtime = build_runtime(config)
    runtime.start()

    # server = MCPServer(runtime)
    # server.start()

    agent = CognitiveAgent(runtime)

    result = agent.run(args.objective)

    print("\n====================")
    print("COGNITIVE RESULT")
    print("====================")

    print("SUCCESS:", result.success)
    print("FIXES:", result.fixes)

    for s in result.steps:
        print(s)


if __name__ == "__main__":
    main()
