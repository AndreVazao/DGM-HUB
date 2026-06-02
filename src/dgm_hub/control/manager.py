from dgm_hub.control.queue import TaskQueue

from dgm_hub.control.task import Task


class TaskManager:

    def __init__(self):

        self.queue = TaskQueue()

    def create_task(

        self,

        objective:str,

        priority:int=1

    ):

        task = Task(

            objective=objective,

            priority=priority

        )

        return self.queue.add(
            task
        )

    def next_task(

        self

    ):

        return self.queue.next_task()