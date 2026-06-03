class ApprovalGate:
    def request_approval(self, plan):
        print("\n=== EXECUTION REQUEST ===\n")
        print("SUMMARY:", plan.summary)
        print("\nFILES:")
        for f in plan.file_changes:
            print("-", f.path)
        print("\nCOMMANDS:")
        for c in plan.commands:
            print("-", c)
        print("\nRISK:", plan.risk_level)
        answer = input("\nAPPROVE? (y/n): ")
        return answer.lower() == "y"
