import time

from dgm_hub.control.manager import TaskManager

from dgm_hub.agent.cognitive_engine import CognitiveAgent


class Worker:

    def __init__(
        self,
        runtime
    ):

        self.runtime = runtime

        self.manager = TaskManager()

        self.agent = CognitiveAgent(
            runtime
        )

    def run(self):

        print(
            "WORKER STARTED"
        )

        while True:

            task = self.manager.next_task()

            if task is None:

                time.sleep(2)

                continue

            print(
                f"[TASK] {task.objective}"
            )

            result = self.agent.run(
                task.objective
            )

            print(result)
