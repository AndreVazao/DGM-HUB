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

## Live DGM-MAT API and end-to-end smoke test

A short-lived local operator session was issued using the existing bootstrap file; only the returned scope names were reported. The secret was not printed or persisted.

- `POST /auth/session`: HTTP 201; scopes `local-client`, `operator`.
- Authenticated `GET /openapi.json`: succeeded.
- `/mobile/threads`: present.
- `/mobile/threads/{thread_id}/messages`: present.
- `/governance/agents/hub/observer/start` and `/stop`: absent in the active DGM-MAT runtime. PR #160 has not yet been promoted to that runtime.
- Pilot Hub home on `127.0.0.1:8771`: HTTP 200; mode selector present.
- Switched the pilot Hub to `respond`; the legacy observer API was correctly reported as `not_installed`, with passive observer disabled.
- Submitted one harmless message: "Olá DGM-MAT. Responde apenas com uma saudação curta."
- Hub task `1d1a5f52-bc0c-4a27-ab41-bb05f44cd4db`: `completed`.
- DGM-MAT provider result: `ok`; source `authenticated_dgm_mat_mobile_runtime`; response returned; `mission_id=null`.
- One dedicated DGM-MAT mobile thread and one Hub journal task were created. No mission, command, repository edit, or external-provider call was triggered. Existing conversation content was not read.
- The pilot server on port 8771 was stopped after the smoke test to conserve memory. Port 8770 and the original active Hub process were left untouched.

## Important operational limitation

The DGM-MAT mobile conversation service attempts local Ollama inference only when at least 1.2 GB of physical memory is available. The latest measured free memory after the pilot was stopped was approximately 515 MB. Therefore this PC uses the service's deterministic intent-response fallback rather than a local LLM response. The authenticated Hub-to-MAT conversation path is proven end to end, but this is not yet a fully capable autonomous reasoning model.

The mission engine auto-approves only its explicit supported read-only intent allowlist. Other work remains subject to the durable approval queue; generic task execution is not complete.

## Deployment boundary

- DGM-HUB PR #31 was merged as `5dd185d`; the new code is in GitHub main.
- The active Hub on port 8770 was not stopped, restarted, or modified and still runs the previous local checkout.
- The DGM-MAT process on port 8181 was not restarted.
- The pilot instance on port 8771 was stopped after successful validation; no extra Hub server is consuming RAM.
- No provider API keys, external provider quotas, external model calls, or paid fallbacks were used. The existing local bootstrap credential was used only to obtain a short-lived local operator session.
