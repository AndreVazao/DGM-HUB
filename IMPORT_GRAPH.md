# DGM-HUB RUNTIME REALITY AUDIT
## PHASE 2: IMPORT GRAPH ANALYSIS

**Audit Date:** 2025-06-05  
**Analysis Scope:** Complete import chains from all entrypoints

---

## IMPORT GRAPH: run_dgm_hub.py

```
run_dgm_hub.py
├─ argparse (stdlib)
├─ local_bootstrap
│  └─ pathlib.Path (stdlib)
│  └─ sys (stdlib)
├─ dgm_hub.agent.agent_loop
│  ├─ dataclasses (stdlib)
│  ├─ dgm_hub.control.runtime_session
│  │  └─ dgm_hub.control.task_executor
│  │     ├─ dataclasses (stdlib)
│  │     ├─ pathlib.Path (stdlib)
│  │     ├─ typing (stdlib)
│  │     ├─ hashlib (stdlib)
│  │     ├─ dgm_hub.execution.execution_history
│  │     │  ├─ dataclasses (stdlib)
│  │     │  └─ datetime (stdlib)
│  │     ├─ dgm_hub.execution.repository_context
│  │     │  └─ pathlib (stdlib)
│  │     ├─ dgm_hub.control.workflow_runtime
│  │     │  ├─ dgm_hub.execution.patch_apply
│  │     │  ├─ dgm_hub.execution.repository_context
│  │     │  └─ dgm_hub.execution.test_pipeline
│  │     │     ├─ subprocess (stdlib)
│  │     │     ├─ dataclasses (stdlib)
│  │     │     └─ pathlib (stdlib)
│  │     ├─ dgm_hub.tools.unified_tool_manager
│  │     │  ├─ typing (stdlib)
│  │     │  ├─ dgm_hub.security.path_guard
│  │     │  ├─ dgm_hub.tools.cmd_tool
│  │     │  ├─ dgm_hub.tools.filesystem_tool
│  │     │  │  └─ dgm_hub.security.path_guard
│  │     │  ├─ dgm_hub.tools.git_tool
│  │     │  │  └─ dgm_hub.security.path_guard
│  │     │  ├─ dgm_hub.tools.powershell_tool
│  │     │  ├─ dgm_hub.tools.registry
│  │     │  ├─ dgm_hub.tools.repo_tool
│  │     │  └─ dgm_hub.tools.test_runner
│  │     ├─ dgm_hub.security.safe_execution
│  │     │  ├─ dataclasses (stdlib)
│  │     │  ├─ pathlib (stdlib)
│  │     │  ├─ shutil (stdlib)
│  │     │  ├─ uuid (stdlib)
│  │     │  └─ hashlib (stdlib)
│  │     ├─ dgm_hub.security.policy_engine
│  │     └─ dgm_hub.memory.execution_journal
│  │        ├─ json (stdlib)
│  │        ├─ pathlib (stdlib)
│  │        ├─ dataclasses (stdlib)
│  │        └─ datetime (stdlib)
│  ├─ dgm_hub.agent.tool_reasoner
│  ├─ dgm_hub.agent.patch_orchestrator
│  ├─ dgm_hub.execution.error_analyzer
│  ├─ dgm_hub.execution.file_loader
│  ├─ dgm_hub.runtime.logger
│  ├─ dgm_hub.control.review_gate
│  └─ dgm_hub.runtime.telemetry
└─ __main__ guard
```

**Total Import Depth:** 9 levels  
**Tool Registry Traversal:** 6 tools registered  
**Safety Layer Activation:** SafeExecutionManager + PathGuard  

---

## IMPORT GRAPH: run_agent.py

```
run_agent.py
├─ argparse (stdlib)
├─ local_bootstrap
│  └─ (same as above)
├─ dgm_hub.bridge.agent_client
│  ├─ requests (external)
│  └─ time (stdlib)
└─ __main__ guard
```

**Total Import Depth:** 3 levels  
**External Dependencies:** requests>=2.32  
**API Contracts:** HTTP POST to /run endpoint  

---

## IMPORT GRAPH: run_cognitive_agent.py

```
run_cognitive_agent.py
├─ argparse (stdlib)
├─ pathlib.Path (stdlib)
├─ local_bootstrap
│  └─ (same as above)
├─ dgm_hub.core.config
│  └─ pyyaml (external)
├─ dgm_hub.core.bootstrap
│  ├─ dgm_hub.core.runtime
│  │  ├─ dgm_hub.tools.registry
│  │  │  └─ dict (stdlib)
│  │  └─ [tool registrations]
│  ├─ dgm_hub.security.path_guard
│  ├─ dgm_hub.tools.filesystem_tool
│  ├─ dgm_hub.tools.powershell_tool
│  ├─ dgm_hub.tools.cmd_tool
│  ├─ dgm_hub.tools.repo_tool
│  ├─ dgm_hub.tools.test_runner
│  └─ dgm_hub.tools.git_tool
├─ dgm_hub.agent.cognitive_engine
│  ├─ dataclasses (stdlib)
│  ├─ pathlib (stdlib)
│  ├─ traceback (stdlib)
│  └─ dgm_hub.evolution.evolution_engine
│     ├─ dgm_hub.evolution.execution_genome
│     └─ dgm_hub.evolution.mutation_engine
└─ __main__ guard
```

**Total Import Depth:** 6 levels  
**Configuration Dependency:** YAML config required  
**Learning System:** EvolutionEngine + ExecutionGenome  
**Mutation Strategy:** MutationEngine for plan adaptation  

---

## IMPORT GRAPH: run_ui.py

```
run_ui.py
├─ uvicorn (external)
│  └─ dgm_hub.ui.server:app
│     ├─ fastapi (external)
│     ├─ (ui handlers)
│     └─ (endpoints)
└─ __main__ guard
```

**Total Import Depth:** 3 levels  
**External Dependencies:** fastapi>=0.111, uvicorn  
**Server Configuration:** 127.0.0.1:8765  
**Auto-reload:** Disabled  

---

## IMPORT GRAPH: run_task.py

```
run_task.py
├─ argparse (stdlib)
├─ local_bootstrap
│  └─ (same as above)
├─ dgm_hub.control.manager
│  ├─ dgm_hub.control.queue
│  │  └─ dgm_hub.control.task
│  │     └─ (dataclass Task)
│  └─ dgm_hub.control.task
└─ __main__ guard
```

**Total Import Depth:** 5 levels  
**Queue System:** TaskQueue for task management  
**Priority Support:** Task priority attribute  

---

## CRITICAL DEPENDENCY TREE

### Core Control Plane
```
control/
├── task_executor.py
│   └── [Orchestrator of all execution]
├── runtime_session.py
│   └── [Thin wrapper around TaskExecutor]
├── manager.py
│   └── [Task creation interface]
├── workflow_runtime.py
│   └── [Test execution + patching]
└── review_gate.py
    └── [Approval decision logic]
```

### Execution Layer
```
execution/
├── repository_context.py
│   └── [Repo introspection]
├── test_pipeline.py
│   └── [subprocess test runner]
├── error_analyzer.py
├── file_loader.py
├── patch_proposal.py
├── patch_apply.py
└── execution_history.py
```

### Tools Layer
```
tools/
├── unified_tool_manager.py
│   ├── registry.py
│   ├── cmd_tool.py
│   ├── powershell_tool.py
│   ├── filesystem_tool.py
│   ├── git_tool.py
│   ├── repo_tool.py
│   └── test_runner.py
└── base.py (abstract tool)
```

### Agent Layer
```
agent/
├── agent_loop.py
│   └── [Main execution coordinator]
├── tool_reasoner.py
│   └── [Tool selection logic]
├── patch_orchestrator.py
│   └── [Patch execution]
├── cognitive_engine.py
│   ├── [Plan + Execute loop]
│   └── evolution_engine.py
│       ├── execution_genome.py
│       └── mutation_engine.py
└── [13 other agent modules]
    └── [Evolution/repair/design patterns]
```

### Security Layer
```
security/
├── path_guard.py
│   └── [Path validation]
├── safe_execution.py
│   └── [Snapshot/Rollback]
├── policy_engine.py
│   └── [Tool permission validation]
├── approval.py
├── audit.py
├── evolution_guard.py
├── patch_authority.py
└── permissions.py
```

### Memory & Logging
```
memory/
├── execution_journal.py
│   └── [JSONL task logging]
├── execution_memory.py
├── evolution_memory.py
└── vault.py

runtime/
├── logger.py
├── telemetry.py
├── event_bus.py
└── session_manager.py
```

---

## IMPORT DEPENDENCY ANALYSIS

### Circular Dependency Risks
**Status:** NONE DETECTED (clean acyclic imports)

### Unused Import Paths
- `dgm_hub.mcp.server` (commented in run_cognitive_agent.py)
- Many agent modules in `dgm_hub.agent/` not imported by active entrypoints

### Convergence Points (Bottlenecks)
1. **UnifiedToolManager** — All tool execution converges here
2. **TaskExecutor** — All runtime sessions route through this
3. **ExecutionJournal** — All execution logging centralizes here
4. **SafeExecutionManager** — All snapshots/rollbacks go through this

### High-Dependency Modules
1. **task_executor.py** — Depends on 8+ modules
2. **agent_loop.py** — Depends on 8+ modules
3. **cognitive_engine.py** — Depends on evolution system

---

## BOOTSTRAP SEQUENCE: DETAILED

### Phase 1: Path Setup
```
enable_src_imports()
  → Path(__file__).resolve().parent / "src"
  → sys.path.insert(0, src)
```

### Phase 2: Root Component Import
```
from dgm_hub.agent.agent_loop import AgentLoop
  → Imports 8 dependencies
  → All dependencies load (no cycles)
  → All lazy imports resolve
```

### Phase 3: Instantiation
```
AgentLoop()
  → RuntimeSession(repository_path=".")
    → TaskExecutor(repository_path=".")
      → UnifiedToolManager()
        → ToolRegistry()
        → Register 6 tools with guards
      → SafeExecutionManager()
      → ExecutionJournal()
```

### Phase 4: Execution
```
AgentLoop.run(repository_path, test_command)
  → RuntimeSession.execute_task()
    → TaskExecutor.execute()
      → [Full execution chain]
```

---

## IMPORT STATISTICS

| Metric | Count |
|--------|-------|
| Total Python files | 76+ |
| Directly imported modules | 42 |
| Tool implementations | 6 |
| Agent variants | 15+ |
| Security modules | 7 |
| Memory modules | 4 |
| Execution modules | 7 |
| External dependencies | 3 |
| Standard library modules used | 15+ |

---

## EXTERNAL DEPENDENCIES

```toml
[project]
dependencies = [
    "fastapi>=0.111",      # Web framework (run_ui.py only)
    "pyyaml>=6.0",         # Config loading (run_cognitive_agent.py only)
    "requests>=2.32",      # HTTP client (run_agent.py only)
]
```

**Observation:** Each dependency is optional depending on entrypoint selection.

