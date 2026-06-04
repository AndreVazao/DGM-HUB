import sys
import tempfile
import time
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.control.protocol_v2 import Action, ExecutionPlan
from dgm_hub.memory.execution_journal import ExecutionJournal
import benchmark_utils as utils

def bench_internal_latencies():
    utils.section("Internal Latencies Benchmark")
    results = utils.load_checkpoint("internal")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        repo = utils.make_repo(tmp_p, "internal-repo", 10, git=True)
        engine = ExecutionEngine(base_dir=repo)
        journal = ExecutionJournal(path=repo / "execution_journal.jsonl")
        
        # 1. Planner Latency (mock)
        if "planner" not in results:
            t0 = time.perf_counter()
            for i in range(1000):
                plan = ExecutionPlan(id=f"plan-{i}", title="test", summary="test",
                                     actions=[Action(type="internal_call", payload={"idx": i})],
                                     risk="low")
            elapsed = time.perf_counter() - t0
            results["planner"] = {"cycles": 1000, "time_s": elapsed, "latency_ms": (elapsed/1000)*1000}
            utils.flush_results("internal", results)
            utils.save_checkpoint("internal", results)
            utils.row("Planner latency (1000 plans)", f"{results['planner']['latency_ms']:.4f} ms/plan")

        # 2. Execution Engine Latency (internal mock actions)
        if "engine" not in results:
            # We measure how long it takes to process 10,000 internal actions
            n_actions = 10000
            actions = [Action(type="internal_call", payload={"idx": i}) for i in range(n_actions)]
            plan = ExecutionPlan(id="engine-plan", title="test", summary="test", actions=actions, risk="low")
            
            t0 = time.perf_counter()
            res = engine.execute(plan)
            elapsed = time.perf_counter() - t0
            
            ok = sum(1 for r in res if r.get("status") == "ok")
            throughput = n_actions / elapsed if elapsed > 0 else 0
            lat_avg = (elapsed / n_actions) * 1000
            
            results["engine"] = {
                "actions": n_actions, "time_s": elapsed, "ok": ok,
                "throughput_cmd_s": throughput, "latency_avg_ms": lat_avg
            }
            utils.flush_results("internal", results)
            utils.save_checkpoint("internal", results)
            utils.row(f"Engine latency ({n_actions} internal actions)", f"{lat_avg:.4f} ms/action")

        # 3. Journal Latency
        if "journal" not in results:
            plan = ExecutionPlan(id="journal-plan", title="test", summary="test",
                                 actions=[Action(type="internal_call", payload={})], risk="low")
            t0 = time.perf_counter()
            for i in range(1000):
                journal.log_plan(plan)
                journal.log_result(plan.id, {"results": [{"action": "internal_call", "status": "ok"}]})
            elapsed = time.perf_counter() - t0
            results["journal"] = {"cycles": 1000, "time_s": elapsed, "latency_ms": (elapsed/1000)*1000}
            utils.flush_results("internal", results)
            utils.save_checkpoint("internal", results)
            utils.row("Journal latency (1000 writes)", f"{results['journal']['latency_ms']:.4f} ms/write")

if __name__ == "__main__":
    print("Running Internal Latencies Benchmark...")
    bench_internal_latencies()
