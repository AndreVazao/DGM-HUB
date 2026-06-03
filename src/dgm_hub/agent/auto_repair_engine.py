class AutoRepairEngine:

    def suggest_fix(self, error_log):
        fixes = []
        for error in error_log:
            if "ModuleNotFoundError" in error:
                fixes.append({
                    "type": "run_command",
                    "cmd": "pip install -r requirements.txt"
                })
            elif "AssertionError" in error:
                fixes.append({
                    "type": "edit_file",
                    "hint": "fix test expectation mismatch"
                })
        return fixes
