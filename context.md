# DGM-HUB Architecture

## Core Components

- **AgentLoop**: Orchestrates the autonomous development cycle.
- **TaskExecutor**: Executes individual tasks with security policy validation.
- **SafeExecutionManager**: Manages filesystem snapshots and rollbacks for safety.
- **PolicyEngine**: Enforces security constraints on tool usage and file paths.
- **ReviewGate**: Gatekeeper for human-in-the-loop approval of code patches.

## MCP Gateway

- **MCPServer**: FastAPI application providing an external interface via the MCP protocol.
- **MCPRouter**: Routes incoming MCP requests to the appropriate runtime tools after policy validation.

## DGM Control Center

- **ExecutionPlan**: Structured data representing a series of actions proposed by the AI.
- **ApprovalGate/Server**: Systems for requesting and managing human approval of execution plans.
- **ExecutionEngine**: Executes approved plans (file writes, shell commands, git operations).
- **PlanDispatcher & WebSocket Server**: Facilitates real-time communication between the backend and UI.
- **UI**: A web-based dashboard for reviewing and approving AI-proposed actions.

## Runtime & Logging

- **RuntimeLogger**: Structured event logging to `runtime/logs.jsonl`.
- **Telemetry**: Real-time event emission to `runtime/telemetry.jsonl`.
- **LiveLogStream**: Live logging for execution feedback.
