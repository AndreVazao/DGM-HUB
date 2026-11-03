from __future__ import annotations

import asyncio
import json

from fastapi.testclient import TestClient

from multichat_journal import EventJournal
import run_multichat as hub


def test_dgm_mat_defaults_to_observer_mode():
    assert hub.DEFAULT_STATE["dgm_mat"]["mode"] == "observer"


def test_dgm_mat_responder_uses_authenticated_runtime_thread(monkeypatch):
    calls = []
    monkeypatch.setattr(hub, "http_online", lambda _url: True)
    monkeypatch.setattr(hub, "_dgm_mat_thread_id", lambda _conversation_id: "thread-test")

    def fake_request(method, path, payload=None):
        calls.append((method, path, payload))
        return {
            "message": "Pedido recebido pelo runtime DGM-MAT.",
            "mission_id": "mission_12345678",
            "intent": {"intent": "audit", "confidence": 0.91},
        }

    monkeypatch.setattr(hub, "_dgm_mat_api_request", fake_request)
    result = hub.run_dgm_mat_responder("Audita o projeto", "conversation-1", "task-1")

    assert result["status"] == "ok"
    assert result["text"] == "Pedido recebido pelo runtime DGM-MAT."
    assert result["mission_id"] == "mission_12345678"
    assert result["thread_id"] == "thread-test"
    assert calls == [
        ("POST", "/mobile/threads/thread-test/messages", {"content": "Audita o projeto"})
    ]


def test_dgm_mat_responder_fails_closed_when_runtime_is_offline(monkeypatch):
    monkeypatch.setattr(hub, "http_online", lambda _url: False)
    monkeypatch.setattr(
        hub,
        "_dgm_mat_api_request",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("API must not be called")),
    )

    try:
        hub.run_dgm_mat_responder("Olá", "conversation-1", "task-1")
    except RuntimeError as exc:
        assert "não está saudável" in str(exc)
    else:
        raise AssertionError("offline DGM-MAT must not return a fabricated answer")


def test_dgm_mat_thread_mapping_is_persistent_and_reused(monkeypatch, tmp_path):
    mapping_path = tmp_path / "dgm_mat_threads.json"
    monkeypatch.setattr(hub, "DGM_MAT_THREAD_MAP_FILE", mapping_path)
    calls = []

    def fake_request(method, path, payload=None):
        calls.append((method, path, payload))
        return {"id": "thread-0123456789abcdef"}

    monkeypatch.setattr(hub, "_dgm_mat_api_request", fake_request)

    first = hub._dgm_mat_thread_id("conversation-1")
    second = hub._dgm_mat_thread_id("conversation-1")

    assert first == second == "thread-0123456789abcdef"
    assert len(calls) == 1
    assert json.loads(mapping_path.read_text(encoding="utf-8")) == {
        "conversation-1": "thread-0123456789abcdef"
    }


def test_dgm_mat_mode_switch_stops_observer_before_persisting_respond(monkeypatch):
    monkeypatch.setitem(hub.PROVIDERS["dgm_mat"], "mode", "observer")
    calls = []
    monkeypatch.setattr(hub, "_set_dgm_mat_observer", lambda active: calls.append(active) or {"stopped": not active})
    monkeypatch.setattr(hub, "save_state", lambda: None)
    client = TestClient(hub.app)

    response = client.post("/api/providers/dgm_mat/mode", json={"mode": "respond"})

    assert response.status_code == 200
    assert response.json()["observer_enabled"] is False
    assert hub.PROVIDERS["dgm_mat"]["mode"] == "respond"
    assert calls == [False]


def test_dgm_mat_mode_switch_is_not_persisted_when_observer_control_fails(monkeypatch):
    monkeypatch.setitem(hub.PROVIDERS["dgm_mat"], "mode", "observer")
    monkeypatch.setattr(
        hub,
        "_set_dgm_mat_observer",
        lambda _active: (_ for _ in ()).throw(RuntimeError("auth unavailable")),
    )
    monkeypatch.setattr(hub, "save_state", lambda: None)
    client = TestClient(hub.app)

    response = client.post("/api/providers/dgm_mat/mode", json={"mode": "respond"})

    assert response.status_code == 503
    assert hub.PROVIDERS["dgm_mat"]["mode"] == "observer"


def test_dgm_mat_mode_rejects_unknown_values():
    client = TestClient(hub.app)
    response = client.post("/api/providers/dgm_mat/mode", json={"mode": "takeover"})
    assert response.status_code == 422


def test_dgm_mat_dispatches_observer_respond_and_hybrid_modes(monkeypatch):
    monkeypatch.setitem(hub.PROVIDERS["dgm_mat"], "mode", "observer")
    monkeypatch.setattr(hub, "run_dgm_observer", lambda *_: {"provider": "dgm_mat", "status": "observer", "text": "observed"})
    monkeypatch.setattr(hub, "run_dgm_mat_responder", lambda *_: {"provider": "dgm_mat", "status": "ok", "text": "answered"})

    assert hub.run_dgm_mat("pedido", "c1", "t1")["status"] == "observer"

    hub.PROVIDERS["dgm_mat"]["mode"] = "respond"
    assert hub.run_dgm_mat("pedido", "c1", "t1")["text"] == "answered"

    hub.PROVIDERS["dgm_mat"]["mode"] = "hybrid"
    hybrid = hub.run_dgm_mat("pedido", "c1", "t1")
    assert hybrid["text"] == "answered"
    assert hybrid["mode"] == "hybrid"
    assert hybrid["observation_recorded"] is True



def test_missing_observer_api_is_reported_as_not_installed_not_as_successful_capture(monkeypatch):
    monkeypatch.setattr(
        hub,
        "_dgm_mat_api_request",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("DGM-MAT API returned HTTP 404 for /governance/agents/hub/observer/stop")),
    )

    result = hub._set_dgm_mat_observer(False)

    assert result["status"] == "not_installed"
    assert result["observer_enabled"] is False
    assert result["requested_enabled"] is False


def test_respond_mode_can_be_selected_when_legacy_runtime_has_no_observer_api(monkeypatch):
    monkeypatch.setitem(hub.PROVIDERS["dgm_mat"], "mode", "observer")
    monkeypatch.setattr(hub, "_set_dgm_mat_observer", lambda _active: {
        "status": "not_installed",
        "observer_enabled": False,
    })
    monkeypatch.setattr(hub, "save_state", lambda: None)
    client = TestClient(hub.app)

    response = client.post("/api/providers/dgm_mat/mode", json={"mode": "respond"})

    assert response.status_code == 200
    assert response.json()["mode"] == "respond"
    assert response.json()["observer_enabled"] is False
    assert hub.PROVIDERS["dgm_mat"]["mode"] == "respond"



def test_hub_chat_persists_the_real_dgm_mat_responder_result(monkeypatch, tmp_path):
    store = EventJournal(tmp_path / "journal.sqlite3", tmp_path / "conversation.jsonl")
    monkeypatch.setattr(hub, "EVENT_STORE", store)
    monkeypatch.setattr(hub, "TASKS", {})
    monkeypatch.setitem(
        hub.PROVIDERS,
        "dgm_mat",
        {"enabled": True, "pid": None, "process_started_at": None, "mode": "respond"},
    )
    monkeypatch.setattr(
        hub,
        "run_dgm_mat_responder",
        lambda message, conversation_id, task_id: {
            "provider": "dgm_mat",
            "status": "ok",
            "text": "Resposta real do runtime MAT: " + message,
            "mission_id": None,
        },
    )

    async def scenario():
        response = await hub.chat(
            hub.ChatRequest(message="Resume o estado", targets=["dgm_mat"], conversation_id="hub-conversation-1")
        )
        pending = [
            task for task in asyncio.all_tasks()
            if task is not asyncio.current_task()
        ]
        if pending:
            await asyncio.gather(*pending)
        return response

    response = asyncio.run(scenario())
    task = store.get_task(response["task_id"])
    events = store.page(after=0, limit=10)["events"]

    assert task["status"] == "completed"
    assert task["results"]["dgm_mat"]["text"] == "Resposta real do runtime MAT: Resume o estado"
    assert [event["kind"] for event in events] == ["user_message", "provider_response"]
    assert all(event["task_id"] == response["task_id"] for event in events)



def test_thread_map_rejects_untrusted_thread_ids(monkeypatch, tmp_path):
    mapping_path = tmp_path / "dgm_mat_threads.json"
    mapping_path.write_text(
        json.dumps({"conversation-1": "../../auth/session"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(hub, "DGM_MAT_THREAD_MAP_FILE", mapping_path)
    monkeypatch.setattr(
        hub,
        "_dgm_mat_api_request",
        lambda method, path, payload=None: {"id": "thread-0123456789abcdef"},
    )

    thread_id = hub._dgm_mat_thread_id("conversation-1")

    assert thread_id == "thread-0123456789abcdef"
    assert json.loads(mapping_path.read_text(encoding="utf-8")) == {
        "conversation-1": "thread-0123456789abcdef"
    }


def test_dgm_mat_api_requests_use_the_configured_runtime_base_url(monkeypatch):
    calls = []
    monkeypatch.setattr(hub, "DGM_MAT_BASE_URL", "http://127.0.0.1:8182")
    monkeypatch.setattr(hub, "_dgm_mat_session_token", lambda: "test-session-token")

    class Response:
        status_code = 200
        def json(self):
            return {"status": "ok"}

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return Response()

    monkeypatch.setattr(hub.requests, "request", fake_request)
    result = hub._dgm_mat_api_request("GET", "/health")

    assert result == {"status": "ok"}
    assert calls[0][1] == "http://127.0.0.1:8182/health"
    assert calls[0][2]["headers"]["Authorization"] == "Bearer test-session-token"
