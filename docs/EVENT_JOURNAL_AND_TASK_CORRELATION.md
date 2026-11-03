# DGM-HUB MultiChat — Durable Event and Task Contract

## Storage

- SQLite at `runtime/multichat/journal.sqlite3` is the authoritative event and task store.
- The existing `conversation.jsonl` remains an append-only compatibility mirror.
- On startup, legacy JSONL lines are migrated idempotently into SQLite. The original file is not rewritten.
- Legacy lines without an event ID receive a deterministic `legacy_<sha256>` ID derived from line number and canonical event content. The ID is persisted in SQLite and remains stable across restarts.
- New events receive a UUID event_id and a monotonically increasing integer seq.

## Event contract

Every event returned by `/api/history` has:

- `event_id`: stable unique event identity.
- `seq`: monotonically increasing sequence used for pagination.
- `timestamp`: UTC ISO-8601 timestamp.
- `kind`: event type.
- `conversation_id` when associated with a conversation.
- `task_id` for user messages and all matching provider response/error events.

Legacy provider events without task_id are retained and marked `correlation_status=legacy_unlinked`; the system does not invent a task relationship.

## Cursor pagination

- `GET /api/history?limit=500` remains compatible and returns the most recent 500 events in ascending sequence order.
- New clients start a full scan with `GET /api/history?after=0&limit=200`.
- `next_cursor` is the sequence number of the final returned event.
- Continue with `after=<next_cursor>` while `has_more=true`.
- Page sizes are restricted to 1–500.
- The SQLite sequence cursor is stable across restart and cannot skip/repeat events when the client advances only to the returned next_cursor.

## Durable task lifecycle

- A task record and its originating user_message event are committed in one SQLite transaction.
- Provider result/error events and updated task results/status are committed together.
- Task state and results survive process restart.
- Tasks left in `queued` or `running` at startup become `interrupted`; they are not automatically re-executed.
- Terminal states: `completed`, `partial`, `failed`, `interrupted`.
- `GET /api/tasks/{task_id}` reads durable state even when the in-memory cache is empty.

## Safety and compatibility

- History reads only SQLite; it never invokes a provider.
- No automatic provider retries or paid fallback were added.
- The existing JSONL file is not deleted or rewritten.
- SQLite uses WAL and FULL synchronous durability.
- Event IDs are unique; repeated insertion with the same event_id is idempotent and cannot overwrite the original payload.

## Validation

The contract tests cover legacy migration, stable IDs, duplicate insertion, >500-event pagination, no gaps/repeats, task correlation, provider error correlation, restart recovery, durable task status and legacy history compatibility.