# DGM-HUB Project Structure

```text
src/dgm_hub/
├── __init__.py
├── agent/
│   ├── __init__.py
│   ├── agent_loop.py           # Unified agent loop (REASONING -> EXECUTION -> DEBUG)
│   ├── patch_intelligence.py   # Heuristic/AI patch generation
│   ├── patch_orchestrator.py   # Patch workflow management
│   ├── tool_reasoner.py        # Context-aware tool selection
│   └── ...
├── control/
│   ├── runtime_session.py      # User session entry point
│   ├── task_executor.py        # Central task execution logic
│   ├── workflow_runtime.py     # Runtime component manager
│   └── ...
├── core/
│   └── ...
├── execution/
│   ├── error_analyzer.py       # Stacktrace and error parsing
│   ├── file_loader.py          # Real file I/O for agents
│   ├── repository_context.py   # Repo structure analyzer
│   ├── test_pipeline.py        # Execution of test commands
│   └── ...
├── tools/
│   ├── registry.py             # Tool registration (by name)
│   ├── unified_tool_manager.py # Unified tool execution layer
│   └── ...
└── ...
```
