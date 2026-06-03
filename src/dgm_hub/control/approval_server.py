from fastapi import FastAPI
from dgm_hub.control.protocol_v2 import ExecutionPlan
from dgm_hub.control.execution_engine import ExecutionEngine

app = FastAPI()
engine = ExecutionEngine()
PENDING_PLANS = {}

@app.post("/submit-plan")
def submit_plan(plan: ExecutionPlan):
    PENDING_PLANS[plan.id] = plan
    return {"status": "waiting_approval", "plan_id": plan.id}

@app.post("/approve/{plan_id}")
def approve(plan_id: str):
    plan = PENDING_PLANS.get(plan_id)
    if not plan:
        return {"error": "not found"}
    engine.execute(plan)
    return {"status": "executed"}

@app.post("/reject/{plan_id}")
def reject(plan_id: str):
    PENDING_PLANS.pop(plan_id, None)
    return {"status": "rejected"}
