import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
import hashlib

import pytest

from dgm_hub.agent.agent_loop import AgentLoop
from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.control.protocol_v2 import Action, ExecutionPlan
from dgm_hub.security.policy_engine import PolicyEngine
from dgm_hub.security.safe_execution import SafeExecutionManager


def init_git(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)


def run_dgm_hub_like(repo: Path, test_command: str | None, monkeypatch):
    workspace = repo.parent
    monkeypatch.chdir(workspace)
    start = time.perf_counter()
    result = AgentLoop().run(str(repo), test_command=test_command)
    duration = time.perf_counter() - start
    return result, duration, workspace


def read_jsonl(path: Path) -> list[dict]:
    assert path.exists(), f"expected JSONL file to exist: {path}"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def assert_runtime_artifacts(workspace: Path, repo: Path, result) -> None:
    logs_path = workspace / "runtime" / "telemetry.jsonl"
    logs = read_jsonl(logs_path)

    repo_hash = hashlib.md5(str(repo.resolve()).encode()).hexdigest()[:8]
    journal_path = workspace / "runtime" / "journals" / f"{repo.name}_{repo_hash}.jsonl"
    journal = read_jsonl(journal_path)

    assert result.context is not None
    assert result.context["root"] == str(repo)
    assert any(entry["event"] == "run_start" for entry in logs)
    assert any(entry["event"] == "run_end" for entry in logs)
    # Check that at least one task_execution or result exists
    assert any(entry["type"] in ["task_execution", "result"] for entry in journal)


def assert_rollback_consistent(repo: Path) -> None:
    tracked = repo / "rollback.txt"
    tracked.write_text("before", encoding="utf-8")

    manager = SafeExecutionManager(str(repo))
    snapshot = manager.create_snapshot(str(repo))

    tracked.write_text("after", encoding="utf-8")
    (repo / "created-after-snapshot.txt").write_text("remove me", encoding="utf-8")

    manager.rollback(snapshot)

    assert tracked.read_text(encoding="utf-8") == "before"
    assert not (repo / "created-after-snapshot.txt").exists()


def test_python_broken_repo_executes_tests_logs_and_rolls_back(tmp_path, monkeypatch):
    repo = tmp_path / "broken-python"
    repo.mkdir()
    init_git(repo)
    (repo / "app.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (repo / "test_app.py").write_text(
        "from app import add\n\n\ndef test_add():\n    assert add(2, 2) == 4\n",
        encoding="utf-8",
    )

    result, duration, workspace = run_dgm_hub_like(
        repo,
        f'"{sys.executable}" -m pytest -q',
        monkeypatch,
    )

    assert result.success is False
    assert result.test_result is not None
    assert result.test_result.return_code != 0
    assert "test_add" in result.test_result.output
    assert result.tool_results
    assert_runtime_artifacts(workspace, repo, result)
    assert_rollback_consistent(repo)
    assert duration < 35


def test_node_broken_repo_executes_tests_logs_and_rolls_back(tmp_path, monkeypatch):
    if shutil.which("node") is None:
        pytest.skip("Node.js is not installed locally")

    repo = tmp_path / "broken-node"
    repo.mkdir()
    init_git(repo)
    (repo / "sum.js").write_text("export function sum(a, b) { return a - b; }\n", encoding="utf-8")
    (repo / "sum.test.mjs").write_text(
        "import test from 'node:test';\n"
        "import assert from 'node:assert/strict';\n"
        "import { sum } from './sum.js';\n\n"
        "test('sum', () => assert.equal(sum(2, 2), 4));\n",
        encoding="utf-8",
    )
    (repo / "package.json").write_text('{"type":"module"}\n', encoding="utf-8")

    result, duration, workspace = run_dgm_hub_like(repo, "node --test", monkeypatch)

    assert result.success is False
    assert result.test_result is not None
    assert result.test_result.return_code != 0
    node_output = result.test_result.output.lower()
    assert "fail 1" in node_output or "assertionerror" in node_output or "not ok" in node_output
    assert_runtime_artifacts(workspace, repo, result)
    assert_rollback_consistent(repo)
    assert duration < 35


def test_large_git_repo_over_1000_files_returns_structured_summary(tmp_path, monkeypatch):
    repo = tmp_path / "large-git"
    repo.mkdir()
    init_git(repo)
    for index in range(1001):
        (repo / f"file_{index:04}.txt").write_text(str(index), encoding="utf-8")

    result, duration, workspace = run_dgm_hub_like(repo, None, monkeypatch)

    assert result.success is True
    assert result.tool_results
    repo_summary = next(item for item in result.tool_results if item["tool"] == "repo_tool")
    assert repo_summary["result"]["summary"]["files"] >= 1001
    assert_runtime_artifacts(workspace, repo, result)
    assert_rollback_consistent(repo)
    assert duration < 35


def test_repo_without_git_does_not_crash_or_call_git(tmp_path, monkeypatch):
    repo = tmp_path / "plain-repo"
    repo.mkdir()
    (repo / "module.py").write_text("VALUE = 1\n", encoding="utf-8")

    result, duration, workspace = run_dgm_hub_like(repo, None, monkeypatch)

    assert result.success is True
    assert all(item["tool"] != "git_tool" for item in result.tool_results or [])
    assert_runtime_artifacts(workspace, repo, result)
    assert_rollback_consistent(repo)
    assert duration < 20


def test_forbidden_paths_are_rejected_with_structured_errors(tmp_path, monkeypatch):
    repo = tmp_path / "forbidden-paths"
    repo.mkdir()
    init_git(repo)

    result, _, workspace = run_dgm_hub_like(repo, None, monkeypatch)
    engine = ExecutionEngine(base_dir=repo)
    plan = ExecutionPlan(
        id="forbidden-paths",
        title="Forbidden paths",
        summary="Attempt writes outside allowed boundaries.",
        actions=[
            Action(type="edit_file", payload={"path": ".git/config", "content": "blocked"}),
            Action(type="edit_file", payload={"path": str(tmp_path / "escape.txt"), "content": "blocked"}),
        ],
        risk="high",
    )

    execution = engine.execute(plan)

    assert result.success is True
    assert all(item["status"] == "error" for item in execution)
    assert all("Path denied" in item["error"] for item in execution)
    assert not (tmp_path / "escape.txt").exists()
    assert_runtime_artifacts(workspace, repo, result)
    assert_rollback_consistent(repo)


def test_protected_files_are_not_leaked_in_tool_outputs(tmp_path, monkeypatch):
    repo = tmp_path / "protected-files"
    repo.mkdir()
    init_git(repo)
    secret = "SUPER_SECRET_TOKEN"
    (repo / ".env").write_text(f"TOKEN={secret}\n", encoding="utf-8")
    (repo / "secrets").mkdir()
    (repo / "secrets" / "key.txt").write_text(secret, encoding="utf-8")
    (repo / "public.py").write_text("print('safe')\n", encoding="utf-8")

    result, _, workspace = run_dgm_hub_like(repo, None, monkeypatch)
    policy = PolicyEngine()

    serialized = json.dumps(result.tool_results or {})
    assert result.success is True
    assert policy.validate_path(".env") is False
    assert policy.validate_path("secrets/key.txt") is False
    assert secret not in serialized
    assert_runtime_artifacts(workspace, repo, result)
    assert_rollback_consistent(repo)


def test_failed_commands_return_structured_output_and_journal(tmp_path, monkeypatch):
    repo = tmp_path / "failed-command"
    repo.mkdir()
    init_git(repo)

    result, _, workspace = run_dgm_hub_like(repo, None, monkeypatch)
    repo_hash = hashlib.md5(str(repo.resolve()).encode()).hexdigest()[:8]
    journal_path = workspace / "runtime" / "journals" / f"{repo.name}_{repo_hash}.jsonl"

    engine = ExecutionEngine(base_dir=repo)
    from dgm_hub.memory.execution_journal import ExecutionJournal
    journal_obj = ExecutionJournal(path=journal_path)

    plan = ExecutionPlan(
        id="failed-command",
        title="Failed command",
        summary="Run command with non-zero exit code.",
        actions=[
            Action(
                type="run_command",
                payload={"cmd": f'"{sys.executable}" -c "import sys; print(\'boom\'); sys.exit(7)"'},
            )
        ],
        risk="low",
    )

    execution = engine.execute(plan, journal=journal_obj)

    assert result.success is True
    assert execution[0]["status"] == "error"
    assert execution[0]["command"]["returncode"] == 7
    assert "boom" in execution[0]["command"]["stdout"]
    assert_runtime_artifacts(workspace, repo, result)
    assert_rollback_consistent(repo)
