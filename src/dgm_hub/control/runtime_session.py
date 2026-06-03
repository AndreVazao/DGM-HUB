from dgm_hub.control.task_executor import TaskExecutor


class RuntimeSession:

    def __init__(self, repository_path: str = "."):

        self.executor = TaskExecutor(repository_path=repository_path)

    def inspect(
        self,
        path:str
    ):

        return self.executor.execute(
            repository_path=path
        )

    def execute_task(
        self,
        repository_path:str,
        test_command:str|None=None
    ):

        return self.executor.execute(
            repository_path=repository_path,
            test_command=test_command
        )
