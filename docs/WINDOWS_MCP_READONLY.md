# Windows MCP — read-only access for DGM-HUB agents

## Purpose

The Windows MCP server is installed locally at:

`C:\\AI\\tools\\windows-mcp-1.3.28\\Sbroenne.WindowsMcp.exe`

DGM-HUB may expose this server to its Codex and Claude Code subprocesses for desktop observation only. It is not a replacement for the DGM-MAT API and it does not grant write access.

## Allowed tools

Only these Windows MCP tools may be enabled:

- `screenshot_control`
- `ui_snapshot`
- `ui_find`
- `ui_read`
- `ui_read_table`
- `ui_wait`

The following classes remain unavailable: clicking, typing, keyboard/mouse input, clipboard writes, window movement/closing, and general window management.

Claude Code uses a strict MCP config and an explicit `--allowedTools` list. Its built-in tools remain disabled with `--tools ""` and it runs in plan mode.

Codex uses the isolated free-only profile under `C:\\AI\\agent-benchmark\\codex-home`, with `sandbox_mode = "read-only"` and the same `enabled_tools` allowlist. Do not copy authentication tokens or the global Codex profile into this isolated profile.

## Local validation

Run `codex mcp list` through the same `codex-free.cmd` wrapper used by DGM-HUB. The `windows` entry must be enabled. A server showing `Auth: Unsupported` is not necessarily a failure for a local stdio server; it means that the CLI does not report an OAuth authentication mode for it.

A provider response is not considered a successful MCP test merely because the server appears in configuration. A real read-only tool call and its result must be independently verified before reporting the integration as operational.

## ChatGPT browser limitation

ChatGPT does not connect directly to a local stdio MCP server. Custom MCP connections use a remote HTTPS endpoint or an available Secure MCP Tunnel. OpenAI currently documents custom MCP read/fetch access for Pro and full write/modify support for Business, Enterprise and Edu; Free is not listed as eligible for custom MCP connections.

Do not expose the Windows MCP listener directly to the public internet. If the account becomes eligible, use OpenAI Secure MCP Tunnel rather than opening an inbound firewall port.

## Safety

- No credentials, tokens, browser cookies, private AI conversation history, or source-code contents are passed to the Windows MCP tools by default.
- Read-only UI observations can still contain private information visible on screen; only invoke them for an explicitly requested task.
- Never enable write-capable Windows MCP tools in the unattended DGM-HUB path without a separate review and explicit operator approval.
