from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

from dgm_hub.core.config import ConfigLoader
from dgm_hub.core.bootstrap import build_runtime


# -----------------------------
# APP INIT
# -----------------------------
app = FastAPI(title="DGM Bridge Server")


# -----------------------------
# GLOBAL RUNTIME
# -----------------------------
config = ConfigLoader("config/default_config.yaml").load()
runtime = build_runtime(config)
runtime.start()


# -----------------------------
# REQUEST MODEL
# -----------------------------
class ToolRequest(BaseModel):
    tool: str
    args: dict


class TaskRequest(BaseModel):
    objective: str


# -----------------------------
# TOOL EXECUTION ENDPOINT
# -----------------------------
@app.post("/tool")
def run_tool(req: ToolRequest):

    tool = runtime.registry.get(req.tool)

    if tool is None:
        return {
            "status": "error",
            "error": f"Tool not found: {req.tool}"
        }

    try:
        result = tool.execute(**req.args)

        return {
            "status": "ok",
            "result": result
        }

    except Exception as e:

        return {
            "status": "error",
            "error": str(e)
        }


# -----------------------------
# HIGH LEVEL TASK EXECUTOR
# -----------------------------
@app.post("/run")
def run_task(req: TaskRequest):

    git = runtime.registry.get("git")
    fs = runtime.registry.get("filesystem")

    repo_path = "C:\\ProgramasGodMode\\DGM-HUB"

    try:

        # STEP 1 - repo status
        status = git.execute(
            operation="status",
            repo_path=repo_path
        )

        # STEP 2 - repo health check
        tree = runtime.registry.get("repo").execute(
            operation="tree",
            repo_path=repo_path
        )

        return {
            "objective": req.objective,
            "status": "ok",
            "git": status,
            "tree_summary": tree.get("summary", {})
        }

    except Exception as e:

        return {
            "status": "error",
            "error": str(e)
        }


# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/health")
def health():

    return {
        "status": "alive",
        "tools": runtime.registry.list_tools()
    }
