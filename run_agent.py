from dgm_hub.bridge.agent_client import AgentClient


def main():

    agent = AgentClient()

    result = agent.execute_loop(
        "audit full repo and fix errors automatically",
        max_iters=5
    )

    print("\n====================")
    print("FINAL STATE")
    print("====================")
    print(result)


if __name__ == "__main__":
    main()
