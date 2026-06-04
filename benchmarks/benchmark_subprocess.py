import sys
import tempfile
import time
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dgm_hub.control.execution_engine import ExecutionEngine
from dgm_hub.control.protocol_v2 import Action, ExecutionPlan
import benchmark_utils as utils

def bench_subprocess():
    utils.section("Subprocess & Execution Benchmarks")
    results = utils.load_checkpoint("subprocess")

    pyexe = sys.executable

    # 1. OS Process Startup Cost (raw subprocess.run vs execution engine)
    if "startup_raw" not in results:
        t0 = time.perf_counter()
        n = 100
        for _ in range(n):
            subprocess.run([pyexe, "-c", "pass"], capture_output=True)
        elapsed = time.perf_counter() - t0
        results["startup_raw"] = {
            "commands": n,
            "time_s": elapsed,
            "latency_ms": (elapsed / n) * 1000
        }
        utils.flush_results("subprocess", results)
        utils.save_checkpoint("subprocess", results)
        utils.row(f"Raw OS Subprocess Startup ({n} cmds)", f"{results['startup_raw']['latency_ms']:.1f} ms/cmd")

    if "execution_engine" not in results:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            repo = utils.make_repo(tmp_p, "exec-repo", 10, git=True)
            engine = ExecutionEngine(base_dir=repo)
            
            n = 100
            actions = [
                Action(type="run_command", payload={"cmd": f'"{pyexe}" -c "pass"'})
                for _ in range(n)
            ]
            plan = ExecutionPlan(id=f"exec-{n}", title=f"exec-{n}", summary="", actions=actions, risk="low")
            
            t0 = time.perf_counter()
            res = engine.execute(plan)
            elapsed = time.perf_counter() - t0
            
            ok = sum(1 for r in res if r["status"] == "ok")
            results["execution_engine"] = {
                "commands": n,
                "time_s": elapsed,
                "latency_ms": (elapsed / n) * 1000,
                "ok": ok
            }
            utils.flush_results("subprocess", results)
            utils.save_checkpoint("subprocess", results)
            utils.row(f"Engine Subprocess Execution ({n} cmds)", f"{results['execution_engine']['latency_ms']:.1f} ms/cmd")

if __name__ == "__main__":
    print("Running Subprocess Benchmark...")
    bench_subprocess()
