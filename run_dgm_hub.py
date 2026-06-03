import argparse
from dgm_hub.agent.agent_loop import AgentLoop

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--test", required=False)
    parser.add_argument("--mode", default="run")
    args = parser.parse_args()

    agent = AgentLoop()
    result = agent.run(
        repository_path=args.repo,
        test_command=args.test
    )

    print("\n===== DGM-HUB RESULT =====\n")
    print("SUCCESS:", result.success)
    print("\nCONTEXT:", result.context)
    print("\nTOOL RESULTS:", result.tool_results)
    print("\nPATCH:", result.patch_result)

    if result.error:
        print("\nERROR:", result.error)

if __name__ == "__main__":
    main()
