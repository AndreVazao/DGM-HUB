import sys
import os
from pathlib import Path

# Add src to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent / "src"))

from dgm_hub.control.protocol_v2 import ExecutionPlan, Action
from dgm_hub.control.execution_engine import ExecutionEngine

def test_execution_engine():
    print("Testing Execution Engine...")
    engine = ExecutionEngine()

    # Define a test file and content
    test_file = "test_e2e_output.txt"
    test_content = "Hello from DGM-HUB E2E Test!"

    plan = ExecutionPlan(
        id="test-1",
        title="Test File Creation",
        summary="Creating a test file to verify the engine.",
        actions=[
            Action(type="edit_file", payload={"path": test_file, "content": test_content})
        ],
        risk="low"
    )

    engine.execute(plan)

    assert Path(test_file).exists()
    assert Path(test_file).read_text() == test_content

    # Cleanup
    os.remove(test_file)
    print("Execution Engine Test Passed!")

if __name__ == "__main__":
    try:
        test_execution_engine()
        print("\nE2E tests completed successfully!")
    except Exception as e:
        print(f"\nE2E tests failed: {e}")
        sys.exit(1)
