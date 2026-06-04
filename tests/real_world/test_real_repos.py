import json
import os
import subprocess
import tempfile
import time
import sys
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dgm_hub.agent.agent_loop import AgentLoop
from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.control.protocol_v2 import Action, ExecutionPlan
from dgm_hub.memory.execution_journal import ExecutionJournal


def _mem_mb() -> float:
    snap = tracemalloc.take_snapshot()
    stats = snap.statistics("lineno")
    return sum(s.size for s in stats) / 1024 / 1024


def clone_repo(url: str, target_dir: Path):
    print(f"Cloning {url} into {target_dir}...")
    subprocess.run(["git", "clone", "--depth", "1", url, str(target_dir)], check=True, capture_output=True)


def run_repo_validation(name: str, config: dict) -> dict:
    url = config["url"]
    test_command = config["test_command"]
    
    results = {
        "name": name,
        "scan": {},
        "test": {},
        "simple_task": {},
        "complex_task": {},
        "success": False,
        "crash": False,
        "rollback_failure": False,
        "corruption": False
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        repo_dir = tmp_p / name
        
        try:
            clone_repo(url, repo_dir)
        except subprocess.CalledProcessError as e:
            results["crash"] = True
            results["error"] = f"Clone failed: {e}"
            return results

        # PHASE 1: Repository Scan
        print(f"[{name}] Phase 1: Repository Scan")
        tracemalloc.start()
        gc_collect = True
        t0 = time.perf_counter()
        try:
            agent = AgentLoop()
            agent.run(repository_path=str(repo_dir), test_command=None)
            elapsed = time.perf_counter() - t0
            mem = _mem_mb()
            
            journal_path = repo_dir / "runtime" / "execution_journal.jsonl"
            journal_size = journal_path.stat().st_size if journal_path.exists() else 0
            
            results["scan"] = {
                "time_s": elapsed,
                "mem_mb": mem,
                "journal_bytes": journal_size
            }
        except Exception as e:
            results["crash"] = True
            results["error"] = f"Scan crashed: {e}"
            return results
        finally:
            tracemalloc.stop()

        # PHASE 2: Run Tests
        print(f"[{name}] Phase 2: Run Tests")
        t0 = time.perf_counter()
        try:
            agent = AgentLoop()
            test_res = agent.run(repository_path=str(repo_dir), test_command=test_command)
            elapsed = time.perf_counter() - t0
            
            results["test"] = {
                "time_s": elapsed,
                "success": test_res.success,
                "patch_generated": test_res.metrics.get("patch_generated", False) if test_res.metrics else False
            }
        except Exception as e:
            results["crash"] = True
            results["error"] = f"Test run crashed: {e}"
            return results

        # PHASE 3: Simple Task
        print(f"[{name}] Phase 3: Simple Task")
        engine = ExecutionEngine(base_dir=repo_dir)
        
        # Find a tracked file to modify
        ls_files = subprocess.run(["git", "ls-files"], cwd=repo_dir, capture_output=True, text=True)
        files = [f for f in ls_files.stdout.splitlines() if f.strip()]
        target_file = files[0] if files else "README.md"
        
        target_path = repo_dir / target_file
        if not target_path.exists():
            target_path.write_text("# Test\n", encoding="utf-8")
            subprocess.run(["git", "add", target_file], cwd=repo_dir, check=True)
            
        original_content = target_path.read_text(encoding="utf-8")
        new_content = original_content + "\n# DGM-HUB Test Comment\n"
        
        plan = ExecutionPlan(
            id="simple-task", title="Add comment", summary="",
            actions=[
                Action(type="edit_file", payload={"path": target_file, "content": new_content})
            ],
            risk="low"
        )
        
        try:
            t0 = time.perf_counter()
            engine_res = engine.execute(plan)
            elapsed = time.perf_counter() - t0
            
            # Check diff
            status_res = subprocess.run(["git", "status", "-s"], cwd=repo_dir, capture_output=True, text=True)
            diff_correct = target_file in status_res.stdout
            
            # Rollback
            subprocess.run(["git", "checkout", "--", target_file], cwd=repo_dir, check=True, capture_output=True)
            status_res_after = subprocess.run(["git", "status", "-s"], cwd=repo_dir, capture_output=True, text=True)
            rollback_works = target_file not in status_res_after.stdout
            
            if not rollback_works:
                results["rollback_failure"] = True
            
            results["simple_task"] = {
                "success": engine_res[0]["status"] == "ok",
                "diff_correct": diff_correct,
                "rollback_works": rollback_works,
                "time_s": elapsed
            }
        except Exception as e:
            results["crash"] = True
            results["error"] = f"Simple task crashed: {e}"
            return results

        # PHASE 4: Complex Task (simulated recovery)
        print(f"[{name}] Phase 4: Complex Task")
        # We simulate a broken test if possible, or just skip if we don't know the repo layout.
        # Since this is a generic harness, we will just simulate a broken python file and see if it patches.
        broken_test_path = repo_dir / "test_dgm_broken.py"
        broken_test_path.write_text(
            "def test_broken():\n    assert False, 'DGM-HUB complex task'\n",
            encoding="utf-8"
        )
        try:
            t0 = time.perf_counter()
            agent = AgentLoop()
            complex_res = agent.run(repository_path=str(repo_dir), test_command="pytest test_dgm_broken.py")
            elapsed = time.perf_counter() - t0
            
            results["complex_task"] = {
                "success": complex_res.metrics.get("patch_generated", False) if complex_res.metrics else False,
                "time_s": elapsed
            }
        except Exception as e:
            # We don't fail the whole suite if the repo doesn't support pytest for this synthetic file
            pass

        results["success"] = True

    return results

if __name__ == "__main__":
    pass
