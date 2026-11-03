# DGM-HUB: Local AI Development Gateway

DGM-HUB is an independent DGM project: a local development gateway for interacting with AI/LLM tooling and coordinating development/debugging workflows.

## Current status in the DGM ecosystem

**DGM-HUB is independent and is NOT part of the DGM-MAT family.**

- **DGM-MAT** is the DGM-MAT family core and the governed digital engineering organization.
- **DGM-HUB** remains an independent local AI gateway and multi-agent discussion room.
- **DGM-MCP** remains an independent MCP project.
- DGM-MAT may observe or consult the Hub through explicit, bounded integration, but the Hub does not depend on DGM-MAT to operate.
- Any deeper integration, agent leadership or repository-writing authority requires a separate architectural decision and explicit operator approval.

This separation prevents historical DGM projects from being absorbed merely because their names contain "DGM".

## Core architecture

The historical autonomous development path is:

**Task** -> **RuntimeSession** -> **TaskExecutor** -> **WorkflowRuntime** -> **UnifiedToolManager** -> **TestPipeline** -> **History**

The local MultiChat cockpit recovered in this branch is an additional, bounded discussion interface. It does not grant providers permission to modify repositories.

## Local MultiChat cockpit (Windows)

### Start without opening a terminal

Run `Start-DGM-HUB-MultiChat.cmd` from this repository. It starts the Hub web server only when the local health endpoint is unavailable and opens the browser at:

http://127.0.0.1:8770

The PowerShell launcher may opportunistically start the DGM-MAT runtime if its local health endpoint is down, so the optional observer can participate. The Hub server itself remains independent and starts even when DGM-MAT is unavailable.

The launcher **does not start Ollama or FCC automatically**. Those providers are controlled by their own Hub controls.

### Providers

- **Codex Free** — invokes the local CLI when a message is sent; it is not a persistent daemon.
- **Claude Code / FCC** — the Hub invokes the local Claude CLI; FCC availability is controlled explicitly. Stopping participation terminates only the FCC process started by this Hub instance; an existing external FCC process is left untouched.
- **Ollama Local** — disabled by default; the Hub can start `ollama serve` only after the operator enables it.
- **DGM-MAT** — optional observer. It can record and respond to the discussion, but it does not lead the room or receive repository-write authority.
- **Kilo Gateway** — optional anonymous free routing through `openrouter/free`; availability and model selection are variable.
- **LLM7** — optional anonymous provider using `gpt-oss:20b`; availability is variable.

The provider selector chooses who responds to the next message. Provider availability controls do not grant filesystem or Git permissions.

### Security boundaries

- The server binds only to `127.0.0.1`; do not expose port 8770 to LAN or the Internet.
- Provider calls are consultative. No provider may modify a repository through this cockpit.
- Codex uses the isolated profile `C:\AI\agent-benchmark\codex-home`.
- Conversation events are journaled under `runtime/multichat/conversation.jsonl`.
- The Hub must not claim a DGM-MAT response unless the authenticated DGM-MAT runtime actually returned one.
- Do not send confidential project material to external free gateways.
- Ollama remains disabled unless explicitly enabled.

## Validation and limitations

- MultiChat status and remaining limitations: `reports/2026-11-02-MULTICHAT-STATUS.md`.
- Free-provider ZIP inventory and security decisions: `reports/2026-11-02-CLONEZIP-AUDIT.md`.
- Stable event IDs, task correlation, cursor pagination and durable task recovery remain tracked separately in DGM-HUB Issue #27.
- Cross-agent debate, decision memory and DGM-MAT's future chairmanship remain staged capabilities, not claims of current autonomy.

## Project structure

See [tree.md](tree.md) for the historical repository structure.
