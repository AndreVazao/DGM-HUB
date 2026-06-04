import json
import time
import statistics
import collections
from pathlib import Path
from test_real_repos import run_repo_validation

def calculate_p95(data):
    if not data: return 0.0
    return sorted(data)[int(len(data) * 0.95)]

def generate_report(summary: dict, report_path: Path):
    lines = ["# Real World Validation Report\n", "## Reliability Metrics\n"]
    total = summary["total_runs"]
    success = summary["total_success"]
    crashes = summary["total_crashes"]
    lines.append(f"- **Total runs:** {total}")
    lines.append(f"- **Successful runs:** {success}")
    lines.append(f"- **Failed runs:** {total - success}")
    lines.append(f"- **Crash Free %:** {( (total - crashes) / total * 100 ) if total else 0:.1f}%\n")
    lines.append("## Recovery Metrics\n")
    lines.append(f"- **Rollback Success %:** {( (total - summary['total_rollback_failures']) / total * 100 ) if total else 0:.1f}%")
    if summary["rollback_times"]:
        lines.append(f"- **Rollback Average Time:** {statistics.mean(summary['rollback_times']):.3f}s")
    lines.append(f"- **Auto Recovery Success %:** {( summary['total_auto_recovery'] / total * 100 ) if total else 0:.1f}%")
    lines.append(f"- **Unrecoverable Failures:** {summary['total_rollback_failures'] + summary['total_corruption']}")
    lines.append(f"- **Human Intervention Count:** {summary['total_human_intervention']}\n")
    lines.append("## Repository Hygiene\n")
    lines.append(f"- **Git Dirty after Execution?** {'Yes' if summary['total_corruption'] > 0 else 'No'}")
    lines.append(f"- **Leaked Files Count:** {summary['total_leaked_files']}\n")
    lines.append("## Resource Metrics\n")
    if summary["mem_ends"]: lines.append(f"- **Peak Memory (approx):** {max(summary['mem_ends']):.2f} MB")
    avg_delta = statistics.mean(summary['mem_deltas']) if summary['mem_deltas'] else 0.0
    lines.append(f"- **Average Memory Delta:** {avg_delta:.2f} MB\n")
    lines.append("## Stability Metrics\n")
    if summary["all_times"]:
        lines.append(f"- **P50 Runtime:** {statistics.median(summary['all_times']):.2f}s")
        lines.append(f"- **P95 Runtime:** {calculate_p95(summary['all_times']):.2f}s")
        lines.append(f"- **Slowest Run:** {max(summary['all_times']):.2f}s\n")
    lines.append("## Confidence Assessment\n")
    rate = success / total if total else 0
    if total > 0 and rate > 0.9 and crashes == 0 and summary['total_corruption'] == 0: lines.append("**HIGH CONFIDENCE**")
    elif total > 0 and rate > 0.6: lines.append("**MEDIUM CONFIDENCE**")
    else: lines.append("**LOW CONFIDENCE**")
    lines.append("\n## Top Failure Causes\n")
    if summary["failure_causes"]:
        for cause, count in summary["failure_causes"].most_common(): lines.append(f"- {cause}: {count}")
    else: lines.append("No failures recorded.")
    lines.append("\n## Per-Repository Breakdown\n")
    for repo_name, metrics in summary["repos"].items():
        lines.append(f"### {repo_name}\n- Success: {metrics['success']}/5\n- Avg Time: {metrics['avg_time']:.2f}s")
        if metrics['errors']: lines.append(f"- Errors: {', '.join(set(metrics['errors']))}")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report generated at {report_path}")

def main():
    base_dir = Path(__file__).parent
    repos_file = base_dir / "repos.json"
    report_file = base_dir / "report.md"
    work_dir = base_dir / "work"
    work_dir.mkdir(exist_ok=True)
    if not repos_file.exists(): return
    repos = json.loads(repos_file.read_text(encoding="utf-8"))
    summary = { "total_runs": 0, "total_success": 0, "total_crashes": 0, "total_rollback_failures": 0, "total_corruption": 0, "total_auto_recovery": 0, "total_human_intervention": 0, "total_leaked_files": 0, "rollback_times": [], "all_times": [], "mem_ends": [], "mem_deltas": [], "failure_causes": collections.Counter(), "repos": {} }
    for name, config in repos.items():
        repo_metrics = {"success": 0, "times": [], "errors": []}
        repo_dir = work_dir / name
        for i in range(1, 6):
            print(f"[{name}] Run {i}/5...")
            res = run_repo_validation(name, config, repo_dir)
            summary["total_runs"] += 1
            if res["success"]: summary["total_success"] += 1; repo_metrics["success"] += 1
            if res["crash"]: summary["total_crashes"] += 1
            if res["rollback_failure"]: summary["total_rollback_failures"] += 1
            if res["corruption"]: summary["total_corruption"] += 1
            if res["recovery_metrics"]["auto_recovery_success"]: summary["total_auto_recovery"] += 1
            summary["total_human_intervention"] += res["human_intervention"]
            summary["total_leaked_files"] += len(res["leaked_files"])
            if res["recovery_metrics"]["rollback_time"] > 0: summary["rollback_times"].append(res["recovery_metrics"]["rollback_time"])
            summary["all_times"].append(res["metrics"]["total_time"])
            repo_metrics["times"].append(res["metrics"]["total_time"])
            summary["mem_ends"].append(res["metrics"]["mem_end"])
            summary["mem_deltas"].append(res["metrics"]["mem_end"] - res["metrics"]["mem_start"])
            if not res["success"]:
                cause = res["error"] or "Unknown Failure"
                if res["recovery_failure"] and not res["error"]: cause = "Auto Recovery Failed"
                if res["rollback_failure"]: cause = "Rollback Failed"
                if res["corruption"]: cause = "Repo Corruption"
                summary["failure_causes"][cause] += 1
                repo_metrics["errors"].append(cause)
        repo_metrics["avg_time"] = statistics.mean(repo_metrics["times"])
        summary["repos"][name] = repo_metrics
    generate_report(summary, report_file)

if __name__ == "__main__":
    main()
