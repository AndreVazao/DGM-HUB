import sys
from pathlib import Path

# Add src to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent / "src"))

from dgm_hub.agent.agent_loop import AgentResult

def test_agent_result_metrics():
    print("Testing AgentResult Metrics...")
    result = AgentResult(
        success=True,
        metrics={"tools_executed": 5, "patch_generated": True}
    )
    assert result.metrics["tools_executed"] == 5
    assert result.metrics["patch_generated"] == True
    print("AgentResult Metrics Test Passed!")

if __name__ == "__main__":
    test_agent_result_metrics()
