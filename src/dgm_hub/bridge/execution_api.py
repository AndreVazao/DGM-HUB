from fastapi import FastAPI
from dgm_hub.control.execution_plan import ExecutionPlan
from dgm_hub.control.approval_gate import ApprovalGate
from dgm_hub.control.executor import Executor

app = FastAPI()
approval_gate = ApprovalGate()
executor = Executor()

@app.post("/execute-plan")
def execute_plan(plan: ExecutionPlan):
    approved = approval_gate.request_approval(plan)
    if not approved:
        return {"status": "rejected"}
    executor.apply_file_changes(plan)
    executor.run_commands(plan)
    executor.git_commit()
    return {"status": "completed"}
