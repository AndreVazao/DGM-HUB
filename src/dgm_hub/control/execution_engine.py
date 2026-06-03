import subprocess
from pathlib import Path

class ExecutionEngine:
    def execute(self, plan, journal=None):
        if journal:
            journal.log_plan(plan)

        results = []
        plan_id = getattr(plan, "id", "unknown")

        for action in plan.actions:
            try:
                if action.type == "edit_file":
                    path = Path(action.payload["path"])
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(action.payload["content"], encoding="utf-8")
                elif action.type in ["run_command", "git", "test"]:
                    # Use check=True to raise CalledProcessError on non-zero exit codes
                    subprocess.run(action.payload["cmd"], shell=True, check=True)
                else:
                    if hasattr(action, "payload") and "cmd" in action.payload:
                        subprocess.run(action.payload["cmd"], shell=True, check=True)
                    else:
                        # If it's a type we don't know and no cmd, it's an error
                        results.append({"action": action.type, "status": "error", "error": f"Unknown action type: {action.type}"})
                        continue

                results.append({"action": action.type, "status": "ok"})
            except Exception as e:
                results.append({"action": action.type, "status": "error", "error": str(e)})

        if journal:
            journal.log_result(plan_id, {"results": results})

        return results
