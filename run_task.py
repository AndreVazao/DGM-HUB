from dgm_hub.control.manager import TaskManager
import sys

def main():

    if len(sys.argv) < 2:

        print(
            "usage: run_task.py objective"
        )

        return

    objective = " ".join(
        sys.argv[1:]
    )

    manager = TaskManager()

    task_id = manager.create_task(
        objective
    )

    print(
        f"created task: {task_id}"
    )


if __name__=="__main__":
    main()
