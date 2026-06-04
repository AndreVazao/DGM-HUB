from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.control.protocol_v2 import Action, ExecutionPlan
from dgm_hub.security.policy_engine import PolicyEngine

def test_policy_engine():
    print("Testing Policy Engine...")
    policy = PolicyEngine()

    # Test blocked paths
    assert policy.validate_path(".git/config") == False
    assert policy.validate_path("src/main.py") == True

    # Test allowed tools
    assert policy.validate_tool("cmd_tool") == True
    assert policy.validate_tool("malicious_tool") == False

    print("Policy Engine Test Passed!")

def test_execution_engine_blocks_dangerous_commands(tmp_path):
    engine = ExecutionEngine(base_dir=tmp_path)
    plan = ExecutionPlan(
        id="security-1",
        title="Blocked Command",
        summary="Attempting to run a destructive command.",
        actions=[
            Action(type="run_command", payload={"cmd": "git reset --hard"})
        ],
        risk="high",
    )

    result = engine.execute(plan)

    assert result[0]["status"] == "error"
    assert "Command denied" in result[0]["error"]
