# DGM-HUB / DGM-MAT responder mode — validation report

**Date:** 2026-11-03  
**Branch:** `feat/dgm-mat-responder-mode-2026-11-03`  
**Base:** `b46b832` — DGM-HUB durable event IDs and task cursor history

## Delivered in this branch

- Added persisted DGM-MAT modes: `observer`, `respond`, and `hybrid`.
- Added a mode selector and apply control to the MultiChat DGM-MAT provider card.
- Added an authenticated local bridge to the existing DGM-MAT mobile conversation API.
- Added in-memory caching of short-lived local operator sessions. The bootstrap credential is read from the existing local file and is never written to Hub state or logs.
- Added a durable, content-free mapping from Hub conversation IDs to DGM-MAT mobile thread IDs.
- Added fail-closed handling for unavailable runtime, invalid responses, authentication failures and non-404 HTTP errors. No automatic retry is made after an ambiguous message POST.
- Added compatibility handling for older DGM-MAT runtimes without the passive observer API. A 404 is reported as `not_installed`; the selected Hub mode is still usable, and the response explicitly reports that passive capture is unavailable.
- Documented the current inference and mission-execution limitations in `docs/DGM-MAT-RESPONDER-MODES.md`.

## Automated validation

- `python -m compileall -q run_multichat.py tests/test_dgm_mat_responder.py`: passed.
- Extracted cockpit JavaScript checked with `node --check`: passed.
- `git diff --check`: passed.
- Focused DGM-MAT responder, durable event contract and Hub safety suites: **27 passed in 23.31s**.

Coverage includes responder dispatch, persistent thread reuse, offline fail-closed behavior, all three modes, failed observer-control state preservation, missing observer API compatibility, invalid mode rejection, thread-ID allowlisting, and the full Hub chat-to-responder durable task/event path.

## Live DGM-MAT API checks

A short-lived local operator session was issued using the existing bootstrap file; only the returned scope names were reported.

- `POST /auth/session`: HTTP 201; scopes `local-client`, `operator`.
- Authenticated `GET /openapi.json`: succeeded.
- `/mobile/threads`: present.
- `/mobile/threads/{thread_id}/messages`: present.
- `/governance/agents/hub/observer/start` and `/stop`: absent in the active DGM-MAT runtime. PR #160 has not yet been promoted to that runtime.
- No mobile thread was created, no message was submitted, no Hub event content was read, and no mission/provider execution was triggered.

## Important operational limitation

The DGM-MAT mobile conversation service attempts local Ollama inference only when at least 1.2 GB of physical memory is available. The latest measured free memory on this PC was approximately 560 MB. Therefore the current machine will take the service's deterministic intent-response fallback rather than a local LLM response. The Hub integration is real and authenticated, but it must not be described as a fully capable autonomous reasoning model yet.

The mission engine auto-approves only its explicit supported read-only intent allowlist. Other work remains subject to the durable approval queue; generic task execution is not complete.

## Deployment boundary

- The active Hub on port 8770 was not stopped, restarted, or modified.
- The active DGM-MAT process on port 8181 was not restarted.
- The responder branch is isolated in a clean worktree and has not been promoted to the active Hub runtime.
- No credentials, provider quotas, external model calls, or paid fallbacks were used.
