import json

class ApprovalInterceptor:
    def request(self, plan):
        print("\n==============================")
        print("DGM-HUB EXECUTION REQUEST")
        print("==============================\n")
        print("TITLE:", plan.title)
        print("\nSUMMARY:", plan.summary)
        print("\nACTIONS:")
        for a in plan.actions:
            print(f"- {a.type}: {json.dumps(a.payload)}")
        print("\nRISK:", plan.risk)
        decision = input("\nAPPROVE? (y/n): ")
        return decision.strip().lower() == "y"
