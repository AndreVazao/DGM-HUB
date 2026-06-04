import unittest
from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.ui.state import STATE
from dataclasses import dataclass

@dataclass
class Action:
    type: str
    payload: dict

@dataclass
class Plan:
    actions: list
    id: str = "test-plan"

class TestExecutionLogger(unittest.TestCase):
    def test_logging(self):
        engine = ExecutionEngine(timeout_seconds=5)
        plan = Plan(actions=[
            Action(type="run_command", payload={"cmd": "echo 'hello world'"})
        ])

        # Clear existing logs
        STATE.logs = []

        engine.execute(plan)

        # Verify that 'hello world' is in the logs
        logs = STATE.get_logs()
        print(f"Captured logs: {logs}")
        self.assertTrue(any("hello world" in log for log in logs))

if __name__ == "__main__":
    unittest.main()
