from dgm_hub.execution.patch_apply import PatchApplyEngine
from dgm_hub.execution.repository_context import RepositoryContextGenerator
from dgm_hub.execution.test_pipeline import TestPipeline


class WorkflowRuntime:

    def __init__(self):

        self.repository = RepositoryContextGenerator()

        self.tests = TestPipeline()

        self.patch_engine = PatchApplyEngine()

    def inspect_repository(
        self,
        path:str
    ):

        return self.repository.build(
            path
        )

    def run_tests(
        self,
        command:str
    ):

        return self.tests.run(
            command
        )
