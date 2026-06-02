class WorkerNode:
    def __init__(self, role, runtime):
        self.role = role
        self.runtime = runtime

    def run(self, task: dict):

        objective = task["objective"]

        if self.role == "planner":
            return {"plan": f"plan for {objective}"}

        if self.role == "executor":
            tool = self.runtime.registry.get("cmd")
            if tool:
                return tool.execute(command=f"echo executing {objective}")
            return {"output": f"executing {objective}"}

        if self.role == "verifier":
            return {"verified": True, "objective": objective}

        return {"noop": True}
