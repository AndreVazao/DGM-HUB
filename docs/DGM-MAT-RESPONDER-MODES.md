# DGM-MAT participation modes in DGM-HUB

**Status:** implementation branch; not yet promoted to the active Hub process.

## Operator controls

The DGM-MAT provider supports three explicit modes, persisted in the Hub provider state:

- `observer`: records each Hub request as a DGM-MAT observation and returns an observation acknowledgement. It does not call the DGM-MAT conversation API.
- `respond`: sends the request to the authenticated local DGM-MAT conversation runtime. It does not record the Hub observation event and requests the passive observer to stop when that API is installed.
- `hybrid`: records the Hub observation and also sends the request to the authenticated DGM-MAT conversation runtime.

The selector is in the DGM-MAT provider card. The Hub endpoint is `POST /api/providers/dgm_mat/mode` with one of `observer`, `respond`, or `hybrid`. Invalid modes are rejected. A mode is persisted only after the observer-control request succeeds or the installed DGM-MAT runtime truthfully reports that the observer API is not installed.

## Local authentication and conversation continuity

- Hub talks only to `http://127.0.0.1:8181`.
- It reads the existing DGM-MAT bootstrap token from `%LOCALAPPDATA%\DGM-MAT\security\bootstrap.token` (or the same `DGM_LOCAL_BOOTSTRAP_FILE` override used by DGM-MAT).
- The bootstrap secret is never written to Hub state, the thread map, or logs.
- A short-lived operator session is cached in memory; it is not persisted.
- Each Hub conversation is mapped to one durable DGM-MAT mobile thread in `runtime/multichat/dgm_mat_threads.json`. The map contains IDs only, not message content.
- Message content and assistant replies remain in the DGM-MAT mobile conversation store.
- A failed/ambiguous POST is not automatically retried. A 404 stale-thread response permits creating a replacement thread because the original thread was confirmed absent.

## Runtime capability and truthful limitations

The DGM-MAT responder calls the existing `/mobile/threads` and `/mobile/threads/{id}/messages` API. That API uses `MobileConversationService`:

- It interprets the request and stores the user/assistant messages.
- It may create a governed mission when the intent classifier marks the request as an execution candidate that does not require approval.
- The mission engine auto-approves only its explicit allowlist of supported read-only intents. Other work remains subject to the durable approval queue and current mission executor support.
- Local Ollama inference is attempted only when the local runtime policy permits it and at least 1.2 GB of physical memory is available. Otherwise the mobile service returns its deterministic intent acknowledgement. The current PC has materially less free memory than that threshold, so this responder must not be advertised as a fully capable local LLM until inference is actually verified or a governed external reasoning path is added.

This feature makes DGM-MAT addressable from the Hub now; it does not claim that generic autonomous code execution is complete.

## Observer API compatibility

The active DGM-MAT runtime currently predates the passive observer API from DGM-MAT PR #160. The Hub checks the observer start/stop route when a mode is applied. HTTP 404 is reported as `not_installed`; other errors fail closed and do not change the selected mode. Once PR #160 is deployed, the same control path starts or stops the real passive observer.

## Validation

The branch includes tests for:
- responder dispatch and durable conversation-thread reuse;
- offline fail-closed behavior;
- all three participation modes;
- observer-control failure not persisting a new mode;
- legacy DGM-MAT runtimes without the passive observer API;
- invalid mode rejection.

External providers (Codex, Claude, Kilo and LLM7) remain consultative. Their output is not granted authority to edit projects or execute commands.
