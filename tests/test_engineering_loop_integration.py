import json
from dataclasses import dataclass
from typing import List, Dict, Any

from dgm_hub.agent.engineering_loop import EngineeringLoop
from dgm_hub.memory.execution_journal import ExecutionJournal

@dataclass
class Action:
    type: str
    payload: Dict[str, Any]

@dataclass
class ExecutionPlan:
    id: str
    title: str
    summary: str
    actions: List[Action]
    risk: str

def test_engineering_loop_integration(tmp_path):
    journal_path = tmp_path / "execution_journal.jsonl"
    loop = EngineeringLoop(journal=ExecutionJournal(journal_path))

    # Create a plan that succeeds
    plan = ExecutionPlan(
        id="test-plan-1",
        title="Test Plan",
        summary="A simple test plan",
        actions=[
            Action(type="run_command", payload={"cmd": "echo 'Hello World'"})
        ],
        risk="low"
    )

    result = loop.run(plan)
    assert result["status"] == "success"
    assert result["iterations"] == 1

    # Verify journal content
    assert journal_path.exists()
    lines = journal_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2 # At least one plan log and one result log

    plan_log = json.loads(lines[0])
    assert plan_log["type"] == "plan"
    assert plan_log["id"] == "test-plan-1"

    result_log = json.loads(lines[1])
    assert result_log["type"] == "result"
    assert result_log["plan_id"] == "test-plan-1"
    assert result_log["result"]["results"][0]["status"] == "ok"

    print("Integration test passed!")

if __name__ == "__main__":
    test_engineering_loop_integration()
