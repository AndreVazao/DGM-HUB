import sys
import tempfile
import time
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.control.protocol_v2 import Action, ExecutionPlan
import benchmark_utils as utils

def bench_stress():
    utils.section("Stress Benchmarks")
    results = utils.load_checkpoint("stress")

    pyexe = sys.executable

    # 1. 100 Cycles Subprocess Stress
    if "subprocess_stress" not in results:
        results["subprocess_stress"] = {"completed_cycles": 0, "latencies": [], "errors": 0}
    
    sub_state = results["subprocess_stress"]
    if sub_state["completed_cycles"] < 100:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            repo = utils.make_repo(tmp_p, "stress-sub-repo", 5, git=True)
            engine = ExecutionEngine(base_dir=repo)
            
            tracker = utils.ETATracker(100)
            tracker.last_log_time = time.perf_counter()
            # Restore state
            tracker.start_time = time.perf_counter() - (mean(sub_state["latencies"]) * sub_state["completed_cycles"] / 1000 if sub_state["latencies"] else 0)

            utils.row("Subprocess Stress", "Resuming/Starting...")
            
            for cycle in range(sub_state["completed_cycles"], 100):
                t0 = time.perf_counter()
                
                plan = ExecutionPlan(
                    id=f"stress-sub-{cycle}", title="sub", summary="sub",
                    actions=[Action(type="run_command", payload={"cmd": f'"{pyexe}" -c "pass"'})],
                    risk="low"
                )
                
                res = engine.execute(plan)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                
                sub_state["latencies"].append(elapsed_ms)
                if res[0]["status"] != "ok":
                    sub_state["errors"] += 1
                    
                sub_state["completed_cycles"] = cycle + 1
                
                if (cycle + 1) % 10 == 0:
                    utils.save_checkpoint("stress", results)
                    utils.flush_results("stress", results)
                    
                eta_log = tracker.update(cycle + 1)
                if eta_log:
                    print(f"  [Subprocess] {eta_log}")
            
            utils.row("Subprocess Stress", "Done!")

    # 2. 10,000 Cycles Internal Stress
    if "internal_stress" not in results:
        results["internal_stress"] = {"completed_cycles": 0, "latencies": [], "errors": 0}
        
    int_state = results["internal_stress"]
    if int_state["completed_cycles"] < 10000:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            repo = utils.make_repo(tmp_p, "stress-int-repo", 5, git=True)
            engine = ExecutionEngine(base_dir=repo)
            
            tracker = utils.ETATracker(10000)
            tracker.last_log_time = time.perf_counter()
            tracker.start_time = time.perf_counter() - (mean(int_state["latencies"]) * int_state["completed_cycles"] / 1000 if int_state["latencies"] else 0)
            
            utils.row("Internal Stress", "Resuming/Starting...")
            
            for cycle in range(int_state["completed_cycles"], 10000):
                t0 = time.perf_counter()
                
                plan = ExecutionPlan(
                    id=f"stress-int-{cycle}", title="int", summary="int",
                    actions=[Action(type="internal_call", payload={"idx": cycle})],
                    risk="low"
                )
                
                res = engine.execute(plan)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                
                int_state["latencies"].append(elapsed_ms)
                if res[0]["status"] != "ok":
                    int_state["errors"] += 1
                    
                int_state["completed_cycles"] = cycle + 1
                
                if (cycle + 1) % 1000 == 0:
                    utils.save_checkpoint("stress", results)
                    utils.flush_results("stress", results)
                    
                eta_log = tracker.update(cycle + 1)
                if eta_log:
                    print(f"  [Internal] {eta_log}")
                    
            utils.row("Internal Stress", "Done!")

if __name__ == "__main__":
    print("Running Stress Benchmark...")
    bench_stress()
