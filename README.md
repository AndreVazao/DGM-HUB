# DGM-HUB: Local AI Development Gateway

DGM-HUB is a modular architecture for autonomous code development and debugging.

## Core Architecture

The system follows a unified execution path:

**Task** -> **RuntimeSession** -> **TaskExecutor** -> **WorkflowRuntime** -> **UnifiedToolManager** -> **TestPipeline** -> **History**

### Features

- **Unified Execution Path**: A single entry point for all agent tasks.
- **Context-Aware Tooling**: The `ToolReasoner` decides which tools to run based on the repository state.
- **Autonomous Debug Loop**:
    1. Run tests.
    2. Parse failures using `ErrorAnalyzer`.
    3. Load real code with `FileLoader`.
    4. Generate targeted fixes with `PatchIntelligenceEngine`.
    5. Orchestrate application with `PatchOrchestrator`.

### Usage

The main entry point for agent operations is the `AgentLoop`:

```python
from dgm_hub.agent.agent_loop import AgentLoop

agent = AgentLoop()
result = agent.run(
    repository_path="./my-repo",
    test_command="pytest"
)
```

## Project Structure

See [tree.md](tree.md) for a detailed view of the codebase.
