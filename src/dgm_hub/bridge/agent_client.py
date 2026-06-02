import requests
import time


class AgentClient:

    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url

    # -----------------------------
    # SEND TASK
    # -----------------------------
    def run_task(self, objective: str):

        payload = {
            "objective": objective
        }

        res = requests.post(
            f"{self.base_url}/run",
            json=payload
        )

        return res.json()

    # -----------------------------
    # TOOL CALL
    # -----------------------------
    def run_tool(self, tool: str, args: dict):

        payload = {
            "tool": tool,
            "args": args
        }

        res = requests.post(
            f"{self.base_url}/tool",
            json=payload
        )

        return res.json()

    # -----------------------------
    # FULL LOOP EXECUTION
    # -----------------------------
    def execute_loop(self, objective: str, max_iters: int = 5):

        state = {
            "objective": objective,
            "iterations": []
        }

        for i in range(max_iters):

            print(f"\n[LOOP] iteration {i}")

            result = self.run_task(objective)

            state["iterations"].append(result)

            # decisão simples de sucesso
            if result.get("status") == "ok" and "error" not in result:

                print("[LOOP] success detected")
                break

            # retry logic
            time.sleep(1)

        return state
