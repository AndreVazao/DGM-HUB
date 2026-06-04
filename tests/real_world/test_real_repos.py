import json
import os
import subprocess
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dgm_hub.agent.agent_loop import AgentLoop
from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.control.protocol_v2 import Action, ExecutionPlan

def _get_mem_mb() -> float:
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0

def clone_repo(url: str, target_dir: Path):
    if target_dir.exists() and (target_dir / ".git").exists():
        return
    print(f"Cloning {url} into {target_dir}...")
    subprocess.run(["git", "clone", "--depth", "1", url, str(target_dir)], check=True, capture_output=True)

def check_corruption(repo_dir: Path) -> list:
    res = subprocess.run(["git", "status", "--porcelain"], cwd=repo_dir, capture_output=True, text=True)
    # Ignore build artifacts and common generated files
    # Also ignore directory deletions/changes that are part of standard build/test of some repos
    lines = [line for line in res.stdout.splitlines() if not any(x in line for x in ["__pycache__", "node_modules", ".pytest_cache", ".egg-info", "dist", "build", "tests/certs"])]
    return lines

def run_repo_validation(name: str, config: dict, repo_dir: Path) -> dict:
    url = config["url"]
    test_command = config["test_command"]
    results = {
        "name": name, "success": False, "crash": False, "rollback_failure": False, "corruption": False,
        "recovery_failure": False, "human_intervention": 0, "leaked_files": [], "error": None,
        "recovery_metrics": {"rollback_time": 0.0, "auto_recovery_success": False},
        "metrics": {"mem_start": 0.0, "mem_end": 0.0, "total_time": 0.0}
    }
    t_total_0 = time.perf_counter()
    try:
        results["metrics"]["mem_start"] = _get_mem_mb()
        if not repo_dir.exists():
            clone_repo(url, repo_dir)

        # Cleanup before start
        subprocess.run(["git", "clean", "-fd"], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "checkout", "."], cwd=repo_dir, capture_output=True)

        print(f"[{name}] Phase 1: Repository Scan")
        AgentLoop().run(repository_path=str(repo_dir), test_command=None)

        print(f"[{name}] Phase 2: Run Tests")
        AgentLoop().run(repository_path=str(repo_dir), test_command=test_command)

        print(f"[{name}] Phase 3: Simple Task")
        engine = ExecutionEngine(base_dir=repo_dir)
        ls_files = subprocess.run(["git", "ls-files"], cwd=repo_dir, capture_output=True, text=True)
        files = [f for f in ls_files.stdout.splitlines() if f.strip() and (f.endswith(".py") or "readme" in f.lower())]
        target_file = files[0] if files else "README.md"
        target_path = repo_dir / target_file
        original_content = target_path.read_text(encoding="utf-8")
        new_content = original_content + "\n# DGM-HUB Validation Comment\n"
        plan = ExecutionPlan(id=f"val-{int(time.time())}", title="Add comment", summary="",
            actions=[Action(type="edit_file", payload={"path": target_file, "content": new_content})], risk="low")
        engine.execute(plan)
        if target_file not in subprocess.run(["git", "status", "-s"], cwd=repo_dir, capture_output=True, text=True).stdout:
            results["corruption"] = True; results["error"] = "Edit not reflected in git status"
        
        t_rb = time.perf_counter()
        subprocess.run(["git", "restore", target_file], cwd=repo_dir, capture_output=True)
        results["recovery_metrics"]["rollback_time"] = time.perf_counter() - t_rb
        
        if target_file in subprocess.run(["git", "status", "-s"], cwd=repo_dir, capture_output=True, text=True).stdout:
             subprocess.run(["git", "checkout", "--", target_file], cwd=repo_dir, capture_output=True)
             if target_file in subprocess.run(["git", "status", "-s"], cwd=repo_dir, capture_output=True, text=True).stdout:
                results["rollback_failure"] = True; results["error"] = "Rollback failed to clear status"
            
        print(f"[{name}] Phase 4: Complex Task")
        target_path_for_fix = (repo_dir / target_file).resolve()
        fake_test = 'python -c "import sys; print(\'File \\"' + str(target_path_for_fix) + '\\", line 1\'); print(\'    Error\'); sys.exit(1)"'
        complex_res = AgentLoop().run(repository_path=str(repo_dir), test_command=fake_test)
        if complex_res.patch_result is not None:
            results["recovery_metrics"]["auto_recovery_success"] = True
            subprocess.run(["git", "restore", str(target_file)], cwd=repo_dir, capture_output=True)
        else:
            results["recovery_failure"] = True
            if isinstance(complex_res.patch_result, dict) and complex_res.patch_result.get("status") == "pending_review":
                results["human_intervention"] += 1

        leaked = check_corruption(repo_dir)
        if leaked:
            results["corruption"] = True; results["leaked_files"] = leaked
        results["metrics"]["mem_end"] = _get_mem_mb()
        results["metrics"]["total_time"] = time.perf_counter() - t_total_0
        results["success"] = not (results["crash"] or results["rollback_failure"] or results["corruption"] or results["recovery_failure"])
    except Exception as e:
        results["crash"] = True; results["error"] = str(e)
    return results
