# DGM-HUB MultiChat local recovery and validation — 2026-11-03

## Recovery source

Recovered the active local cockpit from `C:\AI\DGM-HUB-MultiChat` into a clean worktree based on the latest fetched GitHub main commit.

- Base: `02e41c9b96bae44bc5ce115d14ad14528c9abee2`
- Worktree: `C:\AI\_worktrees\DGM-HUB-MultiChat-recovery-2026-11-03`
- Branch: `recovery/dgm-hub-multichat-2026-11-03`
- Active source checkout remains untouched.
- Recovered: `run_multichat.py`, `multichat.html`, Windows launchers and both 2026-11-02 audit/status reports.
- Backup copies ending in `.bak` and shell crash dumps were intentionally not added to the Git branch.

## Architectural boundary

The README was reconciled with the latest GitHub boundary: DGM-HUB remains an independent DGM project, not part of the DGM-MAT family. DGM-MAT can be an optional observer, but the Hub does not depend on it to run and does not grant it repository-write authority.

The launcher resolves its own repository path, binds the server to loopback, and supports an explicit `DGM_MAT_ROOT` override. It does not start Ollama or FCC automatically.

## Safety correction

The recovered provider shutdown code originally searched for all processes matching the Ollama/FCC executable and could terminate a process that had been started outside the Hub.

The recovery branch now:
- records the PID and process creation time when the Hub starts a provider;
- terminates only a process whose executable path and creation time still match the recorded owner;
- checks the Ollama `serve` command pattern;
- leaves pre-existing external Ollama/FCC processes running when the operator disables Hub participation;
- continues to stop one-shot child processes only through Popen handles owned by the Hub.

## Validation

- Python compile: passed.
- PowerShell AST parse of the Windows launcher: passed.
- FastAPI TestClient `GET /api/health`: HTTP 200.
- FastAPI TestClient `GET /`: HTTP 200.
- Provider/workspace safety tests: **4 passed**.
- No provider was started or stopped during validation.
- No network provider request was sent during validation.

## Outstanding Hub work

The event journal still needs stable event IDs, task correlation and cursor pagination. Those requirements remain tracked in [DGM-HUB Issue #27](https://github.com/AndreVazao/DGM-HUB/issues/27). This recovery PR does not claim to solve durable task recovery or DGM-MAT's future meeting-chair workflow.
