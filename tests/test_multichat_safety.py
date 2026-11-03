from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

import run_multichat as hub


def test_stop_does_not_terminate_preexisting_ollama(monkeypatch):
    entry = {"enabled": True, "pid": None, "process_started_at": None}
    monkeypatch.setitem(hub.PROVIDERS, "ollama", entry)
    monkeypatch.setattr(hub, "http_online", lambda _url: True)
    monkeypatch.setattr(hub, "save_state", lambda: None)
    calls = []
    monkeypatch.setattr(hub, "stop_owned_process", lambda *args, **kwargs: calls.append((args, kwargs)))

    result = hub.stop_provider("ollama")

    assert calls == []
    assert entry["enabled"] is False
    assert "não foi terminado" in result["message"]


def test_stop_terminates_only_persisted_owned_ollama_pid(monkeypatch, tmp_path: Path):
    executable = tmp_path / "ollama.exe"
    executable.write_text("test", encoding="utf-8")
    entry = {"enabled": True, "pid": 4321, "process_started_at": 1234.5}
    monkeypatch.setitem(hub.PROVIDERS, "ollama", entry)
    monkeypatch.setattr(hub.shutil, "which", lambda _name: str(executable))
    monkeypatch.setattr(hub, "http_online", lambda _url: False)
    monkeypatch.setattr(hub, "save_state", lambda: None)
    calls = []

    def stop_owned(*args, **kwargs):
        calls.append((args, kwargs))
        return True

    monkeypatch.setattr(hub, "stop_owned_process", stop_owned)
    hub.stop_provider("ollama")

    assert len(calls) == 1
    assert calls[0][0][0] == 4321
    assert calls[0][0][2] == 1234.5
    assert calls[0][1]["command_pattern"] == "serve"
    assert entry["pid"] is None
    assert entry["process_started_at"] is None


def test_stop_owned_process_refuses_pid_without_creation_time(monkeypatch, tmp_path: Path):
    executable = tmp_path / "fcc-server.exe"
    executable.write_text("test", encoding="utf-8")

    def unexpected_process(_pid):
        raise AssertionError("A PID without ownership metadata must not be inspected or killed")

    monkeypatch.setattr(hub.psutil, "Process", unexpected_process)
    assert hub.stop_owned_process(9876, executable, expected_create_time=None) is False


def test_workspace_cannot_escape_hub_repository(tmp_path: Path):
    with pytest.raises(HTTPException) as exc:
        hub.safe_workspace(str(tmp_path))
    assert exc.value.status_code == 403
