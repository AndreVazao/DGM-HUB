# DGM-HUB: Local AI Development Gateway

DGM-HUB is a modular architecture for autonomous code development and debugging.

## Current status in the DGM ecosystem

**DGM-HUB is currently an independent DGM repository and is NOT part of the DGM-MAT family.**

Its historical purpose is to provide a local development gateway/hub for interacting with local AI/LLM tooling and for running autonomous development/debugging workflows without requiring the user to work directly through terminal windows.

It should therefore be treated as a separate DGM component for now. DGM-MAT may evaluate it later as a reusable capability or integration, but there is no current runtime dependency between DGM-MAT and DGM-HUB.

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

## Relationship with DGM-MAT

DGM-HUB is deliberately left outside the current DGM-MAT consolidation.

For the present architecture:

- **DGM-MAT** is the DGM-MAT family core and is being reconstructed as the governed digital engineering organization.
- **DGM-HUB** remains an independent DGM project.
- **DGM-MCP** remains an independent MCP project and is not modified as part of this consolidation.
- Any future integration must be based on an explicit architectural decision after capability and overlap analysis.

This separation prevents historical DGM projects from being accidentally absorbed merely because their names contain "DGM".
