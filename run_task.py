import argparse
from local_bootstrap import enable_src_imports

enable_src_imports()

from dgm_hub.control.manager import TaskManager

def main():
    parser = argparse.ArgumentParser(description="Create a local DGM-HUB task.")
    parser.add_argument("objective", nargs="+", help="Task objective.")
    parser.add_argument("--priority", type=int, default=1)
    args = parser.parse_args()

    objective = " ".join(
        args.objective
    )

    manager = TaskManager()

    task_id = manager.create_task(
        objective,
        priority=args.priority,
    )

    print(
        f"created task: {task_id}"
    )


if __name__=="__main__":
    main()
