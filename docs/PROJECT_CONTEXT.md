# DGM-HUB Persistent Context

## Mission

Create a local AI development gateway capable of exposing controlled local capabilities to AI systems.

## Primary Goal

Enable iterative development workflows:

AI -> Tools -> Local Execution -> Logs -> AI Analysis -> Repeat

## Architecture Decisions (Locked)

Name:
- DGM-HUB

Platform:
- Windows first
- Headless
- Python 3.12+
- Low resource usage

Communication:
- MCP stdio

Packaging:
- PyInstaller installer

Persistence:
- SQLite
- Dedicated Vault

Security:
- Whitelist model
- Dangerous operations require approval
- Audit logs enabled

## Allowed Paths

- C:\ProgramasGodMode
- C:\AndreOS-Memory
- C:\DevopsGodMode
- C:\AI
- C:\WinZip

## MVP Scope

1. MCP Core
2. Filesystem Tools
3. PowerShell Tools
4. CMD Tools
5. Repo Tools
6. Test Runner
7. Logging Layer
8. Installer

## Runtime Flow

ChatGPT
↓
MCP
↓
Tool Registry
↓
Security Layer
↓
Execution Layer
↓
Logs
↓
ChatGPT

## Resource Constraints

Target machine:
- ~3.2GB RAM
- 2 CPU cores

Optimization priorities:
- Minimal memory usage
- Minimal background CPU
- Small idle footprint

## Development Rule

Prefer architecture stability over rapid refactors.
