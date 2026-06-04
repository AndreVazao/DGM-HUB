import argparse

from local_bootstrap import enable_src_imports

enable_src_imports()

from dgm_hub.bridge.agent_client import AgentClient


def main():
    parser = argparse.ArgumentParser(description="Run a DGM-HUB agent loop through the local bridge.")
    parser.add_argument(
        "objective",
        nargs="?",
        default="audit full repo and fix errors automatically",
        help="Objective to send to the bridge.",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--max-iters", type=int, default=5)
    args = parser.parse_args()

    agent = AgentClient(base_url=args.base_url)

    result = agent.execute_loop(
        args.objective,
        max_iters=args.max_iters,
    )

    print("\n====================")
    print("FINAL STATE")
    print("====================")
    print(result)


if __name__ == "__main__":
    main()
