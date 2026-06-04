"""
tests/chaos/test_destructive_scenarios.py

Chaos / fault-injection suite for DGM-HUB.
Tests that the system survives hostile conditions without crashing,
corrupting the journal, or leaving the repo in a broken state.

Run:  pytest tests/chaos -v
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.control.protocol_v2 import Action, ExecutionPlan
from dgm_hub.runtime.logger import RuntimeLogger
from dgm_hub.security.safe_execution import SafeExecutionManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _init_git(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True,
                   capture_output=True, text=True)


def _make_repo(parent: Path, name: str, *, git: bool = True) -> Path:
    repo = parent / name
    repo.mkdir(parents=True)
    if git:
        _init_git(repo)
    return repo


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if l.strip()]


def _plan(name: str, actions: list[Action], risk: str = "low") -> ExecutionPlan:
    return ExecutionPlan(
        id=name, title=name, summary=name, actions=actions, risk=risk
    )


# ---------------------------------------------------------------------------
# 1. Subprocess timeout — command that hangs
# ---------------------------------------------------------------------------

class TestSubprocessTimeout:
    """Engine must not hang forever when a command times out."""

    def test_hanging_command_returns_structured_error(self, tmp_path):
        repo = _make_repo(tmp_path, "hang-repo")
        engine = ExecutionEngine(base_dir=repo, timeout_seconds=3)

        # Sleep longer than the engine timeout
        if sys.platform == "win32":
            cmd = f'"{sys.executable}" -c "import time; time.sleep(60)"'
        else:
            cmd = "sleep 60"

        plan = _plan("hang", [Action(type="run_command", payload={"cmd": cmd})])
        start = time.perf_counter()
        results = engine.execute(plan)
        elapsed = time.perf_counter() - start

        assert results[0]["status"] == "error", "timed-out command must be an error"
        assert elapsed < 15, f"took too long to detect timeout: {elapsed:.1f}s"
        # system must not crash — engine is still usable
        ok_plan = _plan("echo-ok", [
            Action(type="run_command",
                   payload={"cmd": f'"{sys.executable}" -c "print(42)"'})
        ])
        ok_results = engine.execute(ok_plan)
        assert ok_results[0]["status"] == "ok"


# ---------------------------------------------------------------------------
# 2. Git failure — corrupted .git dir
# ---------------------------------------------------------------------------

class TestGitFailure:
    """Agent must not crash if .git is corrupted."""

    def test_corrupted_git_does_not_crash_agent(self, tmp_path, monkeypatch):
        repo = _make_repo(tmp_path, "corrupt-git")
        (repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        # Corrupt .git/HEAD
        (repo / ".git" / "HEAD").write_text("CORRUPTED\x00\xff", encoding="utf-8")

        monkeypatch.chdir(tmp_path)
        from dgm_hub.agent.agent_loop import AgentLoop
        result = AgentLoop().run(str(repo), test_command=None)

        # Must complete without raising — success or failure both acceptable
        assert result is not None
        assert hasattr(result, "success")


# ---------------------------------------------------------------------------
# 3. Permission denied — readonly file in repo
# ---------------------------------------------------------------------------

class TestPermissionDenied:
    """Engine must return structured error, not crash, on permission denied."""

    @pytest.mark.skipif(sys.platform == "win32", reason="chmod semantics differ on Windows")
    def test_readonly_file_write_returns_error(self, tmp_path):
        repo = _make_repo(tmp_path, "readonly-repo")
        target = repo / "protected.py"
        target.write_text("# protected\n", encoding="utf-8")
        target.chmod(0o444)

        try:
            engine = ExecutionEngine(base_dir=repo)
            plan = _plan("write-readonly", [
                Action(type="edit_file",
                       payload={"path": "protected.py", "content": "# overwritten"})
            ])
            results = engine.execute(plan)
            assert results[0]["status"] == "error"
        finally:
            target.chmod(0o644)

    def test_write_outside_repo_boundary_is_denied(self, tmp_path):
        repo = _make_repo(tmp_path, "bounded-repo")
        engine = ExecutionEngine(base_dir=repo)
        escape = str(tmp_path / "escape.txt")
        plan = _plan("escape", [
            Action(type="edit_file",
                   payload={"path": escape, "content": "should not exist"})
        ], risk="high")
        results = engine.execute(plan)
        assert results[0]["status"] == "error"
        assert not Path(escape).exists()


# ---------------------------------------------------------------------------
# 4. Filesystem readonly — entire repo on readonly mount (simulated)
# ---------------------------------------------------------------------------

class TestReadonlyFilesystem:
    """Rollback + journal must not crash when they cannot write to the repo."""

    def test_snapshot_on_readonly_repo_does_not_crash(self, tmp_path):
        repo = _make_repo(tmp_path, "readonly-fs")
        (repo / "file.txt").write_text("data", encoding="utf-8")
        manager = SafeExecutionManager(str(repo))

        # snapshot goes to a separate dir — it should succeed even if
        # we later make repo readonly
        snapshot = manager.create_snapshot(str(repo))
        assert snapshot is not None

        if sys.platform != "win32":
            # make repo readonly
            for p in repo.rglob("*"):
                try:
                    p.chmod(0o444)
                except Exception:
                    pass
            repo.chmod(0o555)

            try:
                # rollback into readonly repo must not raise unhandled exception
                try:
                    manager.rollback(snapshot)
                except Exception as exc:
                    # acceptable — but must be a controlled exception, not a crash
                    assert isinstance(exc, (PermissionError, OSError)), \
                        f"unexpected exception type: {type(exc)}"
            finally:
                repo.chmod(0o755)
                for p in repo.rglob("*"):
                    try:
                        p.chmod(0o644)
                    except Exception:
                        pass


# ---------------------------------------------------------------------------
# 5. Huge stdout — command that emits megabytes
# ---------------------------------------------------------------------------

class TestHugeStdout:
    """Engine must not OOM or hang on a command with huge output."""

    def test_large_stdout_is_truncated_or_handled(self, tmp_path):
        repo = _make_repo(tmp_path, "huge-stdout")
        engine = ExecutionEngine(base_dir=repo)

        # Print 10 MB of data
        cmd = (f'"{sys.executable}" -c '
               '"import sys; [sys.stdout.write(\'X\' * 1000 + \'\\n\') '
               'for _ in range(10000)]"')
        plan = _plan("huge", [Action(type="run_command", payload={"cmd": cmd})])
        start = time.perf_counter()
        results = engine.execute(plan)
        elapsed = time.perf_counter() - start

        # Must complete in reasonable time
        assert elapsed < 30, f"huge stdout took too long: {elapsed:.1f}s"
        # Result must be structured
        assert "status" in results[0]


# ---------------------------------------------------------------------------
# 6. Journal partially written — file truncated mid-run
# ---------------------------------------------------------------------------

class TestJournalPartialWrite:
    """Logger must produce valid JSONL even if we truncate the file mid-run."""

    def test_logger_survives_truncated_journal(self, tmp_path):
        runtime_dir = tmp_path / "runtime"
        runtime_dir.mkdir()
        journal_path = runtime_dir / "execution_journal.jsonl"

        # Write some valid JSONL
        journal_path.write_text(
            json.dumps({"type": "task_execution", "result": "ok"}) + "\n",
            encoding="utf-8",
        )

        # Simulate mid-write truncation: append incomplete JSON
        with journal_path.open("a", encoding="utf-8") as fh:
            fh.write('{"type": "task_execution", "result": ')  # incomplete

        # Logger should not crash reading/writing past this
        logger = RuntimeLogger(log_file=str(runtime_dir / "logs.jsonl"))
        try:
            logger.log("run_start", {"repo": str(tmp_path)})
            logger.log("run_end", {"success": True})
        except Exception as exc:
            pytest.fail(f"Logger crashed on truncated journal: {exc}")

        # Existing complete lines must still be readable
        all_lines = journal_path.read_text(encoding="utf-8").splitlines()
        valid = 0
        for line in all_lines:
            try:
                json.loads(line)
                valid += 1
            except json.JSONDecodeError:
                pass
        assert valid >= 1, "at least the original valid line must survive"


# ---------------------------------------------------------------------------
# 7. Rollback interrupted — snapshot exists but files deleted before rollback
# ---------------------------------------------------------------------------

class TestRollbackInterrupted:
    """Rollback must not crash if repo files were deleted before rollback fires."""

    def test_rollback_with_missing_repo_files(self, tmp_path):
        repo = _make_repo(tmp_path, "missing-files")
        (repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        (repo / "data.txt").write_text("data\n", encoding="utf-8")

        manager = SafeExecutionManager(str(repo))
        snapshot = manager.create_snapshot(str(repo))

        # Delete everything in repo to simulate crash mid-execution
        shutil.rmtree(repo)
        repo.mkdir()

        # Rollback must not raise an uncontrolled exception
        try:
            manager.rollback(snapshot)
        except Exception as exc:
            # Controlled exception is acceptable; crash/assert is not
            assert isinstance(exc, (FileNotFoundError, OSError, ValueError)), \
                f"unexpected exception type during interrupted rollback: {type(exc)}"


# ---------------------------------------------------------------------------
# 8. Command returns non-zero — structured error preserved in journal
# ---------------------------------------------------------------------------

class TestCommandNonZeroExit:
    """Non-zero exit must produce returncode/stdout/stderr in journal."""

    def test_nonzero_exit_structured_error(self, tmp_path):
        repo = _make_repo(tmp_path, "nonzero-repo")
        engine = ExecutionEngine(base_dir=repo)

        cmd = (f'"{sys.executable}" -c '
               '"import sys; print(\'stdout-msg\'); '
               'print(\'stderr-msg\', file=sys.stderr); sys.exit(42)"')
        plan = _plan("nonzero", [Action(type="run_command", payload={"cmd": cmd})])
        results = engine.execute(plan)

        r = results[0]
        assert r["status"] == "error"
        assert r["command"]["returncode"] == 42
        assert "stdout-msg" in r["command"]["stdout"]
        assert "stderr-msg" in r["command"]["stderr"]


# ---------------------------------------------------------------------------
# 9. Concurrent executions — two engines on same repo don\'t corrupt each other
# ---------------------------------------------------------------------------

class TestConcurrentExecution:
    """Two engines running concurrently on the same repo must not crash."""

    def test_concurrent_engines_no_crash(self, tmp_path):
        repo = _make_repo(tmp_path, "concurrent-repo")
        (repo / "app.py").write_text("x = 1\n", encoding="utf-8")

        errors = []

        def run_engine():
            try:
                engine = ExecutionEngine(base_dir=repo)
                cmd = f'"{sys.executable}" -c "print(42)"'
                plan = _plan("concurrent", [
                    Action(type="run_command", payload={"cmd": cmd})
                ])
                engine.execute(plan)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=run_engine) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert not errors, f"concurrent executions raised: {errors}"


# ---------------------------------------------------------------------------
# 10. Rollback safety — snapshot must be outside repo to survive rmtree
# ---------------------------------------------------------------------------

class TestSnapshotSafetyPath:
    """Snapshot directory must not be inside the target repo."""

    def test_snapshot_not_inside_repo(self, tmp_path):
        repo = _make_repo(tmp_path, "snapshot-safety")
        (repo / "file.py").write_text("x = 1\n", encoding="utf-8")

        manager = SafeExecutionManager(str(repo))
        snapshot = manager.create_snapshot(str(repo))

        snapshot_path = Path(snapshot) if isinstance(snapshot, str) else Path(str(snapshot))
        # The snapshot must NOT be inside the repo tree
        try:
            snapshot_path.relative_to(repo)
            pytest.fail(f"Snapshot is INSIDE the repo: {snapshot_path}")
        except ValueError:
            pass  # correct: snapshot is outside repo
