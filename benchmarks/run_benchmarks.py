"""
benchmarks/run_benchmarks.py

Main runner for the DGM-HUB Benchmark Suite.
"""
import sys
import subprocess
from pathlib import Path

def main():
    benchmarks_dir = Path(__file__).parent
    pyexe = sys.executable

    print("=" * 60)
    print("  DGM-HUB Benchmark Suite")
    print("=" * 60)
    
    scripts = [
        "benchmark_execution_internal.py",
        "benchmark_subprocess.py",
        "benchmark_stress.py"
    ]
    
    for script in scripts:
        print(f"\n--- Running {script} ---\n")
        subprocess.run([pyexe, str(benchmarks_dir / script)])

if __name__ == "__main__":
    main()
