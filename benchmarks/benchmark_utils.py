import json
import os
import time
from pathlib import Path

def get_checkpoint_path(benchmark_name: str) -> Path:
    return Path(__file__).parent / f"checkpoint_{benchmark_name}.json"

def get_results_path(benchmark_name: str) -> Path:
    return Path(__file__).parent / f"results_{benchmark_name}.json"

def load_checkpoint(benchmark_name: str) -> dict:
    path = get_checkpoint_path(benchmark_name)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}

def save_checkpoint(benchmark_name: str, data: dict):
    path = get_checkpoint_path(benchmark_name)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def flush_results(benchmark_name: str, data: dict):
    path = get_results_path(benchmark_name)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

class ETATracker:
    def __init__(self, total_iterations: int):
        self.total_iterations = total_iterations
        self.start_time = time.perf_counter()
        self.last_log_time = self.start_time
        
    def update(self, current_iteration: int) -> str | None:
        """Returns an ETA string periodically, or None if not time yet."""
        now = time.perf_counter()
        if now - self.last_log_time >= 5.0 or current_iteration == self.total_iterations: # Log every 5 seconds
            elapsed = now - self.start_time
            if current_iteration > 0:
                avg_time_per_iter = elapsed / current_iteration
                remaining_iters = self.total_iterations - current_iteration
                eta_seconds = remaining_iters * avg_time_per_iter
                
                self.last_log_time = now
                progress = (current_iteration / self.total_iterations) * 100
                return f"Progress: {current_iteration}/{self.total_iterations} ({progress:.1f}%) - ETA: {eta_seconds:.1f}s"
        return None

def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def row(label: str, value: str) -> None:
    print(f"  {label:<45} {value}")

def init_git(repo: Path) -> None:
    import subprocess
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)

def make_repo(parent: Path, name: str, n_files: int, git: bool = True) -> Path:
    repo = parent / name
    repo.mkdir(parents=True, exist_ok=True)
    if git:
        init_git(repo)
    for i in range(n_files):
        (repo / f"file_{i:05}.txt").write_text(str(i), encoding="utf-8")
    return repo
