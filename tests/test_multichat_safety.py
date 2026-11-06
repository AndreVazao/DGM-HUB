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

def test_run_claude_uses_verified_fcc_launcher_and_readonly_windows_mcp(monkeypatch, tmp_path: Path):
    import json

    launcher = tmp_path / "fcc-claude.exe"
    launcher.write_text("test", encoding="utf-8")
    windows_exe = tmp_path / "Sbroenne.WindowsMcp.exe"
    windows_exe.write_text("test", encoding="utf-8")
    mcp_config = tmp_path / "windows-readonly-mcp.json"
    monkeypatch.setattr(hub, "CLAUDE_EXE", launcher)
    monkeypatch.setattr(hub, "WINDOWS_MCP_EXE", windows_exe)
    monkeypatch.setattr(hub, "CLAUDE_MCP_CONFIG", mcp_config)
    monkeypatch.setattr(hub, "http_online", lambda _url: True)
    monkeypatch.setattr(hub, "CLAUDE_CLI_VERIFIED", False)
    captured = {}

    def fake_run_cli(command, prompt, cwd, provider, timeout=150, env=None):
        captured.update(
            command=command,
            prompt=prompt,
            cwd=cwd,
            provider=provider,
            timeout=timeout,
            env=env,
        )
        return {
            "provider": "claude",
            "text": "FCC response",
            "status": "ok",
            "response_verified": True,
        }

    monkeypatch.setattr(hub, "run_cli", fake_run_cli)
    result = hub.run_claude("one bounded test", tmp_path)

    assert result["status"] == "ok"
    assert captured["command"][0] == str(launcher)
    assert "--bare" in captured["command"]
    assert "--strict-mcp-config" in captured["command"]
    assert "--no-session-persistence" in captured["command"]
    assert captured["command"][captured["command"].index("--tools") + 1] == ""
    allowed = captured["command"][captured["command"].index("--allowedTools") + 1].split(",")
    assert allowed == [f"mcp__windows__{name}" for name in hub.WINDOWS_MCP_READ_ONLY_TOOLS]
    assert not any(name.endswith(("ui_click", "ui_type", "window_management")) for name in allowed)
    config = json.loads(mcp_config.read_text(encoding="utf-8"))
    assert config["mcpServers"]["windows"]["command"] == str(windows_exe)
    assert config["mcpServers"]["windows"]["args"] == []
    assert captured["prompt"] == "one bounded test"
    assert captured["provider"] == "claude"
    assert captured["timeout"] == 150
    assert captured["env"]["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:8082"
    assert captured["env"]["ANTHROPIC_AUTH_TOKEN"] == "freecc"
    assert mcp_config.is_file()
    assert hub.CLAUDE_CLI_VERIFIED is True


def test_run_claude_keeps_empty_mcp_when_windows_server_is_missing(monkeypatch, tmp_path: Path):
    import json

    launcher = tmp_path / "fcc-claude.exe"
    launcher.write_text("test", encoding="utf-8")
    missing_windows_exe = tmp_path / "missing" / "Sbroenne.WindowsMcp.exe"
    mcp_config = tmp_path / "windows-readonly-mcp.json"
    monkeypatch.setattr(hub, "CLAUDE_EXE", launcher)
    monkeypatch.setattr(hub, "WINDOWS_MCP_EXE", missing_windows_exe)
    monkeypatch.setattr(hub, "CLAUDE_MCP_CONFIG", mcp_config)
    monkeypatch.setattr(hub, "http_online", lambda _url: True)
    captured = {}

    def fake_run_cli(command, prompt, cwd, provider, timeout=150, env=None):
        captured["command"] = command
        return {"provider": "claude", "text": "response", "status": "ok", "response_verified": True}

    monkeypatch.setattr(hub, "run_cli", fake_run_cli)
    hub.run_claude("bounded test", tmp_path)

    assert "mcp__windows__" not in " ".join(captured["command"])
    assert json.loads(mcp_config.read_text(encoding="utf-8")) == {"mcpServers": {}}


def test_run_claude_timeout_does_not_mark_provider_verified(monkeypatch, tmp_path: Path):
    launcher = tmp_path / "fcc-claude.exe"
    launcher.write_text("test", encoding="utf-8")
    monkeypatch.setattr(hub, "CLAUDE_EXE", launcher)
    monkeypatch.setattr(hub, "CLAUDE_MCP_CONFIG", tmp_path / "empty-mcp.json")
    monkeypatch.setattr(hub, "http_online", lambda _url: True)
    monkeypatch.setattr(hub, "CLAUDE_CLI_VERIFIED", False)

    def fail_run_cli(*args, **kwargs):
        raise RuntimeError("provider timeout")

    monkeypatch.setattr(hub, "run_cli", fail_run_cli)
    with pytest.raises(RuntimeError, match="provider timeout"):
        hub.run_claude("one bounded test", tmp_path)

    assert hub.CLAUDE_CLI_VERIFIED is False

