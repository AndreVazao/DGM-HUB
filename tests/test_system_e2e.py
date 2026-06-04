from dgm_hub.control.protocol_v2 import ExecutionPlan, Action
from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.tools.repo_tool import RepoTool
from dgm_hub.tools.unified_tool_manager import UnifiedToolManager

def test_execution_engine(tmp_path):
    print("Testing Execution Engine...")
    engine = ExecutionEngine(base_dir=tmp_path)

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

    result = engine.execute(plan)

    assert result == [{"action": "edit_file", "status": "ok"}]
    assert (tmp_path / test_file).exists()
    assert (tmp_path / test_file).read_text() == test_content

    print("Execution Engine Test Passed!")

def test_execution_engine_blocks_paths_outside_base(tmp_path):
    engine = ExecutionEngine(base_dir=tmp_path)
    outside = tmp_path.parent / "outside.txt"
    plan = ExecutionPlan(
        id="test-2",
        title="Blocked File Creation",
        summary="Attempting to create a file outside the allowed root.",
        actions=[
            Action(type="edit_file", payload={"path": str(outside), "content": "blocked"})
        ],
        risk="high"
    )

    result = engine.execute(plan)

    assert result[0]["status"] == "error"
    assert "Path denied" in result[0]["error"]
    assert not outside.exists()


def test_execution_engine_blocks_git_paths(tmp_path):
    engine = ExecutionEngine(base_dir=tmp_path)
    plan = ExecutionPlan(
        id="test-3",
        title="Blocked Git File Creation",
        summary="Attempting to write into .git.",
        actions=[
            Action(type="edit_file", payload={"path": ".git/config", "content": "blocked"})
        ],
        risk="high"
    )

    result = engine.execute(plan)

    assert result[0]["status"] == "error"
    assert "Path denied" in result[0]["error"]


def test_unified_tool_manager_registers_default_aliases(tmp_path):
    manager = UnifiedToolManager(allowed_paths=[str(tmp_path)])

    assert manager.registry.get("repo_tool") is not None
    assert manager.registry.get("repo") is manager.registry.get("repo_tool")


def test_repo_tool_summary(tmp_path):
    (tmp_path / "example.py").write_text("print('ok')", encoding="utf-8")
    result = RepoTool().execute(operation="summary", repo_path=str(tmp_path))

    assert result["summary"]["files"] == 1
