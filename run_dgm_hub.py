import argparse
import sys
from pathlib import Path
from local_bootstrap import enable_src_imports

enable_src_imports()

from dgm_hub.agent.agent_loop import AgentLoop

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--test", required=False)
    parser.add_argument("--mode", default="run")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        print(f"ERROR: Repository path does not exist: {repo_path}")
        sys.exit(1)
    if not repo_path.is_dir():
        print(f"ERROR: Repository path is not a directory: {repo_path}")
        sys.exit(1)

    print(f"Starting DGM-HUB on: {repo_path}")

    agent = AgentLoop()
    result = agent.run(
        repository_path=str(repo_path),
        test_command=args.test
    )

    print("\n===== DGM-HUB RESULT =====\n")
    print("SUCCESS:", result.success)
    print("\nCONTEXT:", result.context)
    print("\nTOOL RESULTS:", result.tool_results)
    print("\nTEST RESULT:", result.test_result)
    print("\nPATCH:", result.patch_result)

    if result.error:
        print("\nERROR:", result.error)

if __name__ == "__main__":
    main()
