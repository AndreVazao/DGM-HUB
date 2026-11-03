from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi.testclient import TestClient

from multichat_journal import EventJournal


def _task(task_id: str = "task-1", status: str = "queued") -> dict:
    return {
        "task_id": task_id,
        "conversation_id": "conversation-1",
        "targets": ["codex", "llm7"],
        "completed": [],
        "results": {},
        "created_at": "2026-11-03T12:00:00+00:00",
        "status": status,
    }


def test_legacy_jsonl_migrates_with_stable_ids_without_rewriting_source(tmp_path):
    legacy = tmp_path / "conversation.jsonl"
    original = (
        json.dumps({"kind": "user_message", "conversation_id": "c1", "message": "hello"}) + "\n"
        + json.dumps({"kind": "provider_response", "conversation_id": "c1", "provider": "codex", "text": "hi"}) + "\n"
    )
    legacy.write_text(original, encoding="utf-8")

    first = EventJournal(tmp_path / "journal.sqlite3", legacy)
    first_page = first.page(after=0, limit=10)
    first_ids = [event["event_id"] for event in first_page["events"]]

    second = EventJournal(tmp_path / "journal.sqlite3", legacy)
    second_page = second.page(after=0, limit=10)

    assert len(first_ids) == 2
    assert all(event_id.startswith("legacy_") for event_id in first_ids)
    assert [event["event_id"] for event in second_page["events"]] == first_ids
    assert [event["seq"] for event in second_page["events"]] == [1, 2]
    assert all(event["correlation_status"] == "legacy_unlinked" for event in second_page["events"])
    assert legacy.read_text(encoding="utf-8") == original


def test_new_event_id_is_persisted_and_mirrored_to_legacy_jsonl(tmp_path):
    legacy = tmp_path / "conversation.jsonl"
    store = EventJournal(tmp_path / "journal.sqlite3", legacy)
    record = store.append({
        "kind": "user_message",
        "task_id": "task-1",
        "conversation_id": "conversation-1",
        "message": "Inventariar o Hub",
    })

    reopened = EventJournal(tmp_path / "journal.sqlite3", legacy)
    loaded = reopened.page(after=0, limit=10)["events"][0]
    mirrored = json.loads(legacy.read_text(encoding="utf-8").splitlines()[-1])

    assert record["event_id"] == loaded["event_id"] == mirrored["event_id"]
    assert record["seq"] == loaded["seq"] == mirrored["seq"] == 1
    assert loaded["task_id"] == "task-1"


def test_cursor_pagination_reads_more_than_500_events_without_gaps_or_repeats(tmp_path):
    store = EventJournal(tmp_path / "journal.sqlite3")
    total = 1207
    for index in range(total):
        store.append({
            "kind": "provider_response",
            "task_id": f"task-{index // 3}",
            "conversation_id": f"conversation-{index // 20}",
            "provider": "codex",
            "message_index": index,
        })

    cursor = "0"
    sequences = []
    event_ids = []
    page_count = 0
    while True:
        page = store.page(after=cursor, limit=173)
        page_count += 1
        sequences.extend(event["seq"] for event in page["events"])
        event_ids.extend(event["event_id"] for event in page["events"])
        if not page["has_more"]:
            break
        assert page["next_cursor"] is not None
        cursor = page["next_cursor"]

    assert page_count == 7
    assert sequences == list(range(1, total + 1))
    assert len(event_ids) == len(set(event_ids)) == total

    legacy_window = store.page(limit=500)
    assert len(legacy_window["events"]) == 500
    assert legacy_window["events"][0]["seq"] == total - 499
    assert legacy_window["events"][-1]["seq"] == total
    assert legacy_window["cursor_mode"] == "latest_window"


def test_task_and_origin_event_commit_atomically_and_results_survive_restart(tmp_path):
    store = EventJournal(tmp_path / "journal.sqlite3")
    task = _task()
    store.create_task(task, {
        "kind": "user_message",
        "task_id": task["task_id"],
        "conversation_id": task["conversation_id"],
        "message": "Implementar event_id",
    })

    task["completed"] = ["codex"]
    task["results"] = {"codex": {"status": "ok", "text": "Proposta concluída"}}
    task["status"] = "partial"
    store.save_task_and_event(task, {
        "kind": "provider_response",
        "task_id": task["task_id"],
        "conversation_id": task["conversation_id"],
        "provider": "codex",
        "status": "ok",
        "text": "Proposta concluída",
    })

    reopened = EventJournal(tmp_path / "journal.sqlite3")
    restored = reopened.get_task("task-1")
    events = reopened.page(after=0, limit=10)["events"]

    assert restored is not None
    assert restored["status"] == "partial"
    assert restored["results"]["codex"]["text"] == "Proposta concluída"
    assert len(events) == 2
    assert all(event["task_id"] == "task-1" for event in events)
    assert events[0]["kind"] == "user_message"
    assert events[1]["kind"] == "provider_response"


def test_restart_marks_incomplete_tasks_interrupted_and_preserves_completed_results(tmp_path):
    store = EventJournal(tmp_path / "journal.sqlite3")
    running = _task("running-task", "running")
    running["completed"] = ["codex"]
    running["results"] = {"codex": {"status": "ok", "text": "saved"}}
    store.save_task(running)

    completed = _task("completed-task", "completed")
    completed["completed"] = ["codex", "llm7"]
    completed["results"] = {
        "codex": {"status": "ok", "text": "one"},
        "llm7": {"status": "ok", "text": "two"},
    }
    store.save_task(completed)

    restarted = EventJournal(tmp_path / "journal.sqlite3")
    assert restarted.recover_incomplete_tasks() == 1
    tasks = restarted.load_tasks()

    assert tasks["running-task"]["status"] == "interrupted"
    assert tasks["running-task"]["results"]["codex"]["text"] == "saved"
    assert tasks["completed-task"]["status"] == "completed"


def test_duplicate_event_id_is_idempotent(tmp_path):
    store = EventJournal(tmp_path / "journal.sqlite3")
    first = store.append({
        "event_id": "stable-event-1",
        "kind": "user_message",
        "task_id": "task-1",
        "conversation_id": "c1",
        "message": "original",
    })
    second = store.append({
        "event_id": "stable-event-1",
        "kind": "user_message",
        "task_id": "task-1",
        "conversation_id": "c1",
        "message": "changed retry must not overwrite",
    })

    events = store.page(after=0, limit=10)["events"]
    assert first == second
    assert len(events) == 1
    assert events[0]["message"] == "original"


def test_chat_links_user_message_and_provider_result_to_same_durable_task(monkeypatch, tmp_path):
    import run_multichat as hub

    store = EventJournal(tmp_path / "journal.sqlite3", tmp_path / "conversation.jsonl")
    monkeypatch.setattr(hub, "EVENT_STORE", store)
    monkeypatch.setattr(hub, "TASKS", {})
    monkeypatch.setitem(hub.PROVIDERS, "dgm_mat", {"enabled": True, "pid": None, "process_started_at": None})
    monkeypatch.setattr(
        hub,
        "run_dgm_observer",
        lambda message, conversation_id, task_id: {
            "provider": "dgm_mat",
            "status": "observer",
            "text": "observação registada",
        },
    )

    async def scenario():
        result = await hub.chat(
            hub.ChatRequest(message="Registar a decisão", targets=["dgm_mat"])
        )
        pending = [
            task for task in asyncio.all_tasks()
            if task is not asyncio.current_task()
        ]
        if pending:
            await asyncio.gather(*pending)
        return result

    response = asyncio.run(scenario())
    events = store.page(after=0, limit=10)["events"]
    task_id = response["task_id"]

    assert events[0]["kind"] == "user_message"
    assert events[0]["task_id"] == task_id
    provider_events = [
        event for event in events
        if event["kind"] in {"provider_response", "provider_error"}
    ]
    assert len(provider_events) == 1
    assert provider_events[0]["task_id"] == task_id
    assert store.get_task(task_id)["status"] == "completed"


def test_history_api_supports_cursor_and_keeps_legacy_limit_contract(monkeypatch, tmp_path):
    import run_multichat as hub

    store = EventJournal(tmp_path / "journal.sqlite3")
    for index in range(5):
        store.append({"kind": "user_message", "conversation_id": "c1", "message": str(index)})
    monkeypatch.setattr(hub, "EVENT_STORE", store)
    client = TestClient(hub.app)

    first = client.get("/api/history", params={"after": 0, "limit": 2})
    second = client.get("/api/history", params={"after": first.json()["next_cursor"], "limit": 2})
    legacy = client.get("/api/history", params={"limit": 500})

    assert first.status_code == second.status_code == legacy.status_code == 200
    assert [item["seq"] for item in first.json()["events"]] == [1, 2]
    assert first.json()["has_more"] is True
    assert [item["seq"] for item in second.json()["events"]] == [3, 4]
    assert legacy.json()["events"][-1]["seq"] == 5
    assert "next_cursor" in legacy.json()


def test_history_api_rejects_invalid_cursor_and_out_of_range_limit(monkeypatch, tmp_path):
    import run_multichat as hub

    store = EventJournal(tmp_path / "journal.sqlite3")
    monkeypatch.setattr(hub, "EVENT_STORE", store)
    client = TestClient(hub.app)

    assert client.get("/api/history", params={"after": "not-a-cursor"}).status_code == 422
    assert client.get("/api/history", params={"limit": 501}).status_code == 422


def test_task_status_reads_durable_task_after_in_memory_cache_is_empty(monkeypatch, tmp_path):
    import run_multichat as hub

    store = EventJournal(tmp_path / "journal.sqlite3")
    task = _task("persisted-task", "completed")
    task["completed"] = ["codex", "llm7"]
    task["results"] = {"codex": {"status": "ok"}, "llm7": {"status": "ok"}}
    store.save_task(task)
    monkeypatch.setattr(hub, "EVENT_STORE", store)
    monkeypatch.setattr(hub, "TASKS", {})
    client = TestClient(hub.app)

    response = client.get("/api/tasks/persisted-task")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["done"] is True
    assert response.json()["results"]["codex"]["status"] == "ok"


def test_provider_error_event_keeps_originating_task_id_and_terminal_state(monkeypatch, tmp_path):
    import run_multichat as hub

    store = EventJournal(tmp_path / "journal.sqlite3")
    task = {
        "task_id": "error-task",
        "conversation_id": "error-conversation",
        "targets": ["llm7"],
        "completed": [],
        "results": {},
        "created_at": "2026-11-03T12:00:00+00:00",
        "status": "queued",
    }
    store.create_task(task, {
        "kind": "user_message",
        "task_id": "error-task",
        "conversation_id": "error-conversation",
        "message": "Testar erro",
    })
    monkeypatch.setattr(hub, "EVENT_STORE", store)
    monkeypatch.setattr(hub, "TASKS", {"error-task": task})

    def fail_provider():
        raise RuntimeError("HTTP 429")

    asyncio.run(
        hub.execute_provider(
            "error-task",
            "error-conversation",
            "llm7",
            fail_provider,
        )
    )

    events = store.page(after=0, limit=10)["events"]
    error_events = [event for event in events if event["kind"] == "provider_error"]
    restored = store.get_task("error-task")

    assert len(error_events) == 1
    assert error_events[0]["task_id"] == "error-task"
    assert error_events[0]["provider"] == "llm7"
    assert error_events[0]["status"] == "error"
    assert restored["status"] == "failed"
    assert restored["results"]["llm7"]["text"].startswith("RuntimeError")
