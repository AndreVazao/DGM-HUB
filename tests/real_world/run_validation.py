import json
from pathlib import Path
from test_real_repos import run_repo_validation

def generate_report(results: list, report_path: Path):
    lines = [
        "# Real World Validation Report\n",
        "This report summarizes the execution of DGM-HUB against real-world repositories.\n",
        "## Summary Statistics\n"
    ]
    
    total = len(results)
    success = sum(1 for r in results if r["success"])
    crashes = sum(1 for r in results if r.get("crash", False))
    rollback_failures = sum(1 for r in results if r.get("rollback_failure", False))
    
    lines.append(f"- **Total Repositories:** {total}")
    lines.append(f"- **Overall Success Rate:** {success}/{total} ({(success/total*100) if total else 0:.1f}%)")
    lines.append(f"- **Crash Rate:** {crashes}/{total} ({(crashes/total*100) if total else 0:.1f}%)")
    lines.append(f"- **Rollback Failures:** {rollback_failures}/{total}")
    lines.append("\n## Detailed Results\n")
    
    for r in results:
        lines.append(f"### {r['name']}\n")
        if r.get("crash"):
            lines.append(f"**CRASHED:** {r.get('error', 'Unknown Error')}\n")
            continue
            
        scan = r.get("scan", {})
        test = r.get("test", {})
        simple = r.get("simple_task", {})
        complex_t = r.get("complex_task", {})
        
        lines.append("#### 1. Repository Scan")
        lines.append(f"- Time: {scan.get('time_s', 0):.2f}s")
        lines.append(f"- Peak Memory: {scan.get('mem_mb', 0):.2f} MB")
        lines.append(f"- Journal Size: {scan.get('journal_bytes', 0) / 1024:.2f} KB\n")
        
        lines.append("#### 2. Run Tests")
        lines.append(f"- Time: {test.get('time_s', 0):.2f}s")
        lines.append(f"- Success: {'Yes' if test.get('success') else 'No'}")
        lines.append(f"- Patch Generated: {'Yes' if test.get('patch_generated') else 'No'}\n")
        
        lines.append("#### 3. Simple Task (Add Comment)")
        lines.append(f"- Time: {simple.get('time_s', 0):.2f}s")
        lines.append(f"- Engine Success: {'Yes' if simple.get('success') else 'No'}")
        lines.append(f"- Diff Correct: {'Yes' if simple.get('diff_correct') else 'No'}")
        lines.append(f"- Rollback Works: {'Yes' if simple.get('rollback_works') else 'No'}\n")
        
        lines.append("#### 4. Complex Task (Simulated Error Recovery)")
        lines.append(f"- Time: {complex_t.get('time_s', 0):.2f}s")
        lines.append(f"- Recovery Success: {'Yes' if complex_t.get('success') else 'No'}\n")
        
        lines.append("---\n")
        
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report generated at {report_path}")

def main():
    base_dir = Path(__file__).parent
    repos_file = base_dir / "repos.json"
    report_file = base_dir / "report.md"
    
    if not repos_file.exists():
        print("repos.json not found.")
        return
        
    repos = json.loads(repos_file.read_text(encoding="utf-8"))
    results = []
    
    print("=" * 60)
    print("Starting Real World Validation...")
    print("=" * 60)
    
    for name, config in repos.items():
        print(f"\n--- Testing {name} ---")
        res = run_repo_validation(name, config)
        results.append(res)
        
    print("\n" + "=" * 60)
    print("Validation Complete. Generating report...")
    generate_report(results, report_file)
    print("=" * 60)

if __name__ == "__main__":
    main()
