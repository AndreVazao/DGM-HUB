"""Durable DGM-HUB MultiChat event journal and task state.

SQLite is the source of truth. The historical JSONL file remains a readable,
append-only compatibility mirror and is migrated without being rewritten.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class EventJournal:
    """Persist stable event IDs, monotonic sequence cursors and durable task state."""

    def __init__(self, database_path: str | Path, legacy_jsonl_path: str | Path | None = None):
        self.database_path = Path(database_path)
        self.legacy_jsonl_path = Path(legacy_jsonl_path) if legacy_jsonl_path else None
        self._lock = threading.RLock()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        if self.legacy_jsonl_path:
            self.legacy_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        self._migrate_legacy_jsonl()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=15)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    task_id TEXT,
                    conversation_id TEXT,
                    kind TEXT,
                    timestamp TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_task_id ON events(task_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_conversation_seq "
                "ON events(conversation_id, seq)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_conversation "
                "ON tasks(conversation_id, created_at)"
            )

    @staticmethod
    def _insert_event(
        connection: sqlite3.Connection, event: dict[str, Any]
    ) -> tuple[dict[str, Any], bool]:
        record = dict(event)
        record.pop("seq", None)
        record.setdefault("timestamp", _utc_now())
        record.setdefault("event_id", str(uuid.uuid4()))
        event_id = str(record["event_id"])
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO events
                (event_id, task_id, conversation_id, kind, timestamp, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                record.get("task_id"),
                record.get("conversation_id"),
                record.get("kind"),
                str(record["timestamp"]),
                "{}",
            ),
        )
        created = cursor.rowcount == 1
        if created:
            record["seq"] = int(cursor.lastrowid)
            connection.execute(
                "UPDATE events SET payload_json=? WHERE seq=?",
                (_json(record), record["seq"]),
            )
            return record, True

        existing = connection.execute(
            "SELECT payload_json FROM events WHERE event_id=?", (event_id,)
        ).fetchone()
        if existing is None:
            raise RuntimeError("Event insert was ignored but its stable event_id was not found.")
        return json.loads(existing["payload_json"]), False

    @staticmethod
    def _upsert_task(connection: sqlite3.Connection, task: dict[str, Any]) -> dict[str, Any]:
        record = dict(task)
        task_id = record.get("task_id")
        conversation_id = record.get("conversation_id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id is required for durable task state")
        if not isinstance(conversation_id, str) or not conversation_id:
            raise ValueError("conversation_id is required for durable task state")
        record.setdefault("created_at", _utc_now())
        record["updated_at"] = _utc_now()
        record.setdefault("status", "queued")
        connection.execute(
            """
            INSERT INTO tasks(task_id, conversation_id, created_at, updated_at, status, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                conversation_id=excluded.conversation_id,
                updated_at=excluded.updated_at,
                status=excluded.status,
                payload_json=excluded.payload_json
            """,
            (
                task_id,
                conversation_id,
                str(record["created_at"]),
                str(record["updated_at"]),
                str(record["status"]),
                _json(record),
            ),
        )
        return record

    def _mirror_legacy(self, record: dict[str, Any]) -> None:
        if self.legacy_jsonl_path is None:
            return
        try:
            with self._lock, self.legacy_jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(_json(record) + "\n")
                handle.flush()
        except OSError:
            # SQLite remains authoritative; a mirror failure must not erase a durable event.
            return

    def _migrate_legacy_jsonl(self) -> int:
        path = self.legacy_jsonl_path
        if path is None or not path.is_file():
            return 0
        migrated = 0
        with self._lock, path.open("r", encoding="utf-8", errors="replace") as source:
            with self._connection() as connection:
                for line_number, line in enumerate(source, start=1):
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    if not isinstance(record.get("event_id"), str) or not record["event_id"]:
                        digest_input = f"{line_number}\0{_json(record)}".encode("utf-8")
                        record["event_id"] = "legacy_" + hashlib.sha256(digest_input).hexdigest()
                    if (
                        not record.get("task_id")
                        and record.get("kind") in {"user_message", "provider_response", "provider_error"}
                    ):
                        record.setdefault("correlation_status", "legacy_unlinked")
                    _stored, created = self._insert_event(connection, record)
                    migrated += int(created)
        return migrated

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._connection() as connection:
            record, created = self._insert_event(connection, event)
        if created:
            self._mirror_legacy(record)
        return record

    def create_task(self, task: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
        if event.get("task_id") != task.get("task_id"):
            raise ValueError("The originating event must carry the same task_id as the task record.")
        with self._lock, self._connection() as connection:
            self._upsert_task(connection, task)
            record, created = self._insert_event(connection, event)
        if created:
            self._mirror_legacy(record)
        return record

    def save_task(self, task: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._connection() as connection:
            return self._upsert_task(connection, task)

    def save_task_and_event(
        self, task: dict[str, Any], event: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if event.get("task_id") != task.get("task_id"):
            raise ValueError("The provider event must carry the same task_id as the task record.")
        with self._lock, self._connection() as connection:
            stored_task = self._upsert_task(connection, task)
            stored_event, created = self._insert_event(connection, event)
        if created:
            self._mirror_legacy(stored_event)
        return stored_task, stored_event

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def load_tasks(self) -> dict[str, dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM tasks ORDER BY created_at, task_id"
            ).fetchall()
        tasks = {}
        for row in rows:
            task = json.loads(row["payload_json"])
            tasks[task["task_id"]] = task
        return tasks

    def recover_incomplete_tasks(self) -> int:
        tasks = self.load_tasks()
        recovered = 0
        for task in tasks.values():
            if task.get("status") in {"queued", "running"}:
                task["status"] = "interrupted"
                task["interrupted_at"] = _utc_now()
                self.save_task(task)
                recovered += 1
        return recovered

    def page(self, *, after: str | int | None = None, limit: int = 100) -> dict[str, Any]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        with self._connection() as connection:
            total = int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])
            if after is None:
                rows = connection.execute(
                    "SELECT payload_json FROM events ORDER BY seq DESC LIMIT ?", (limit,)
                ).fetchall()
                rows = list(reversed(rows))
                has_more = False
                mode = "latest_window"
            else:
                try:
                    cursor = int(after)
                except (TypeError, ValueError) as exc:
                    raise ValueError("after must be a numeric sequence cursor") from exc
                if cursor < 0:
                    raise ValueError("after must be zero or greater")
                rows = connection.execute(
                    "SELECT payload_json FROM events WHERE seq>? ORDER BY seq ASC LIMIT ?",
                    (cursor, limit + 1),
                ).fetchall()
                has_more = len(rows) > limit
                rows = rows[:limit]
                mode = "cursor"
        events = [json.loads(row["payload_json"]) for row in rows]
        next_cursor = str(events[-1]["seq"]) if events else (str(after) if after is not None else None)
        return {
            "events": events,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "total_events": total,
            "cursor_mode": mode,
        }
