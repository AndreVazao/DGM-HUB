# DGM-HUB RUNTIME REALITY AUDIT
## PHASE 1: ENTRYPOINT DISCOVERY REPORT

**Audit Date:** 2025-06-05  
**Repository:** C:\ProgramasGodMode\DGM-HUB  
**Platform:** Windows (Python 3.12+)

---

## ENTRYPOINTS DISCOVERED

### 1. **run_dgm_hub.py** — Main Agent Loop Entrypoint
**Path:** `/run_dgm_hub.py`  
**Purpose:** Execute full DGM-HUB agent workflow on a repository  
**Type:** CLI executable

**Signature:**
```python
main()
```

**Arguments:**
- `--repo` (required): Repository path
- `--test` (optional): Test command
- `--mode` (default="run"): Execution mode

**Bootstrap Chain:**
```
run_dgm_hub.py
  ↓ local_bootstrap.enable_src_imports()
  ↓ dgm_hub.agent.agent_loop.AgentLoop
  ↓ Runtime instantiation
```

**Runtime Path:**
```
AgentLoop.run(repository_path, test_command)
  → RuntimeSession.execute_task()
  → TaskExecutor.execute()
```

**Output Structure:**
```python
AgentResult(
    success: bool,
    context: dict,
    tool_results: list,
    test_result: Any,
    patch_result: Any,
    error: str | None,
    metrics: dict
)
```

---

### 2. **run_agent.py** — Bridge Client Entrypoint
**Path:** `/run_agent.py`  
**Purpose:** Execute agent through HTTP bridge/API  
**Type:** CLI executable (requires running bridge server)

**Signature:**
```python
main()
```

**Arguments:**
- `objective` (optional, default="audit full repo and fix errors automatically"): Task objective
- `--base-url` (default="http://127.0.0.1:8000"): Bridge server URL
- `--max-iters` (default=5): Maximum iterations

**Bootstrap Chain:**
```
run_agent.py
  ↓ local_bootstrap.enable_src_imports()
  ↓ dgm_hub.bridge.agent_client.AgentClient
  ↓ HTTP client initialization
```

**Runtime Path:**
```
AgentClient.execute_loop(objective, max_iters)
  → AgentClient.run_task(objective)
  → HTTP POST /run
```

**Output Structure:**
```python
{
    "objective": str,
    "iterations": [result1, result2, ...],
    "status": "ok" | "error"
}
```

---

### 3. **run_cognitive_agent.py** — Cognitive Engine Entrypoint
**Path:** `/run_cognitive_agent.py`  
**Purpose:** Execute autonomous cognitive agent with learning loop  
**Type:** CLI executable (standalone)

**Signature:**
```python
main()
```

**Arguments:**
- `objective` (optional, default="audit git repo and fix issues automatically"): Agent objective
- `--config` (default="config/default_config.yaml"): Configuration file

**Bootstrap Chain:**
```
run_cognitive_agent.py
  ↓ local_bootstrap.enable_src_imports()
  ↓ ConfigLoader
  ↓ build_runtime(config)
  ↓ CognitiveAgent initialization
```

**Runtime Path:**
```
ConfigLoader.load()
  ↓ build_runtime(config)
    → Runtime()
    → Register tools (FilesystemTool, PowerShellTool, CmdTool, etc.)
  ↓ CognitiveAgent.run(objective)
```

**Output Structure:**
```python
CognitiveState(
    objective: str,
    success: bool,
    steps: list,
    memory: dict,
    errors: list,
    fixes: int
)
```

---

### 4. **run_ui.py** — Web UI Server Entrypoint
**Path:** `/run_ui.py`  
**Purpose:** Start FastAPI web interface server  
**Type:** Server executable

**Signature:**
```python
uvicorn.run(
    "dgm_hub.ui.server:app",
    host="127.0.0.1",
    port=8765,
    reload=False
)
```

**Runtime Environment:**
- Host: `127.0.0.1`
- Port: `8765`
- Auto-reload: Disabled

**Bootstrap Chain:**
```
run_ui.py
  ↓ uvicorn.run()
  ↓ dgm_hub.ui.server:app (FastAPI app)
```

---

### 5. **run_task.py** — Task Creation Entrypoint
**Path:** `/run_task.py`  
**Purpose:** Create a task in the task queue  
**Type:** CLI executable

**Signature:**
```python
main()
```

**Arguments:**
- `objective` (positional, variadic): Task objective (multiple words)
- `--priority` (default=1): Task priority

**Bootstrap Chain:**
```
run_task.py
  ↓ local_bootstrap.enable_src_imports()
  ↓ dgm_hub.control.manager.TaskManager
```

**Runtime Path:**
```
TaskManager.create_task(objective, priority)
  → Returns task_id
```

**Output:**
```
created task: {task_id}
```

---

### 6. **src/dgm_hub/main.py** — Library Entrypoint
**Path:** `/src/dgm_hub/main.py`  
**Purpose:** Main module export  
**Type:** Library module (not directly executable)

**Usage:**
```python
from dgm_hub import main
```

---

### 7. **local_bootstrap.py** — Bootstrap Entrypoint
**Path:** `/local_bootstrap.py`  
**Purpose:** Enable src/ imports for all CLI entrypoints  
**Type:** Utility module

**Function:**
```python
enable_src_imports() -> None
```

**Effect:** Adds `./src` to `sys.path` for proper module discovery

---

## BOOTSTRAP SEQUENCE ANALYSIS

### Standard Bootstrap (CLI Entrypoints)
```
1. Import local_bootstrap
2. Call enable_src_imports()
   → Adds ./src to sys.path
3. Import from dgm_hub.* modules
4. Instantiate root component
5. Execute main() logic
```

### Configuration Bootstrap (run_cognitive_agent.py)
```
1. enable_src_imports()
2. ConfigLoader loads YAML config
3. build_runtime(config)
   → Creates Runtime instance
   → Registers all tools with path guards
4. CognitiveAgent initialization
5. Main loop execution
```

### Server Bootstrap (run_ui.py)
```
1. No local_bootstrap call (direct import)
2. uvicorn.run() starts server
3. FastAPI app initialization
4. Listen on 127.0.0.1:8765
```

---

## DEPENDENCY ANALYSIS

### Direct Dependencies (from pyproject.toml)
```
fastapi >= 0.111
pyyaml >= 6.0
requests >= 2.32
```

### Tool Registration Pattern
All entrypoints funnel through `UnifiedToolManager`:
- FilesystemTool (with PathGuard)
- CmdTool
- PowerShellTool
- RepoTool
- TestRunnerTool
- GitTool (with PathGuard)

---

## EXECUTION GRAPH SUMMARY

```
┌─────────────────────────────────────────┐
│         CLI ENTRYPOINTS                 │
├─────────────────────────────────────────┤
│                                         │
│  run_dgm_hub.py ──→ AgentLoop          │
│  run_agent.py ──→ AgentClient (HTTP)   │
│  run_cognitive_agent.py ──→ CognitiveAgent
│  run_ui.py ──→ FastAPI Server          │
│  run_task.py ──→ TaskManager           │
│                                         │
└────────────────┬────────────────────────┘
                 │
           ┌─────┴──────┐
           │             │
    ┌──────▼─────┐  ┌───▼──────┐
    │ TaskExecutor│  │ CognitiveAgent
    │  (sync)    │  │ (learning loop)
    └──────┬─────┘  └───┬──────┘
           │            │
      ┌────▼────────────▼────┐
      │   UnifiedToolManager  │
      │   (tool dispatch)     │
      └──────┬────────────────┘
             │
      ┌──────┴──────────────────────┬──────────┐
      │                             │          │
  ┌───▼────┐  ┌────────┐  ┌────────▼──┐  ┌──▼──┐
  │Filesys │  │ Git    │  │PowerShell │  │Repo │
  │Tool    │  │Tool    │  │Tool       │  │Tool │
  └────────┘  └────────┘  └───────────┘  └─────┘
```

---

## CRITICAL OBSERVATIONS

1. **Multi-path Architecture**: Five distinct entry mechanisms exist
   - Direct execution (run_dgm_hub.py)
   - HTTP bridge (run_agent.py)
   - Cognitive loop (run_cognitive_agent.py)
   - Server UI (run_ui.py)
   - Task creation (run_task.py)

2. **Bootstrap Pattern**: All CLI tools use `enable_src_imports()` except run_ui.py

3. **Tool Centralization**: All execution converges on `UnifiedToolManager`

4. **Configuration**: Only cognitive_agent uses YAML configuration loading

5. **Safety Layer**: `PathGuard` integrated in tool registration

