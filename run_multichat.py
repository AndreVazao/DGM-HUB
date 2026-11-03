from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import psutil
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import requests
from fastapi import FastAPI, HTTPException, Query
from multichat_journal import EventJournal
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "runtime" / "multichat"
DATA_DIR.mkdir(parents=True, exist_ok=True)
JOURNAL = DATA_DIR / "conversation.jsonl"
EVENT_STORE = EventJournal(DATA_DIR / "journal.sqlite3", JOURNAL)
STATE_FILE = DATA_DIR / "providers.json"
HTML_FILE = ROOT / "multichat.html"

OLLAMA_URL = os.getenv("DGM_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("DGM_OLLAMA_MODEL", "qwen2.5-coder:1.5b")
KILO_URL = "https://api.kilo.ai/api/gateway"
KILO_MODEL = "openrouter/free"
LLM7_URL = "https://api.llm7.io/v1"
LLM7_MODEL = "gpt-oss:20b"
CODEX_CMD = r"C:\AI\bin\codex-free.cmd"
FCC_SERVER_EXE = Path.home() / ".local" / "bin" / "fcc-server.exe"
CLAUDE_EXE = Path.home() / ".local" / "bin" / "fcc-claude.exe"
CLAUDE_NODE_EXE = Path(r"C:\Program Files\nodejs\node.exe")
CLAUDE_CLI_JS = Path.home() / "AppData" / "Local" / "ClaudeCode-JS-2.1.112" / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
CLAUDE_MCP_CONFIG = DATA_DIR / "empty-mcp.json"
DGM_MAT_ROOT = Path(r"C:\ProgramasGodMode\DGM-MAT")
DGM_MAT_BASE_URL = os.getenv("DGM_MAT_BASE_URL", "http://127.0.0.1:8181").strip().rstrip("/")
DGM_MAT_HEALTH = DGM_MAT_BASE_URL + "/health"
DGM_MAT_THREAD_MAP_FILE = DATA_DIR / "dgm_mat_threads.json"
_DGM_MAT_LOCK = threading.RLock()
_DGM_MAT_SESSION: dict[str, Any] = {"token": None, "expires_at": 0.0}
FCC_HEALTH = "http://127.0.0.1:8082/admin"

DEFAULT_STATE = {
    "codex": {"enabled": True, "pid": None, "process_started_at": None},
    "claude": {"enabled": False, "pid": None, "process_started_at": None},
    "ollama": {"enabled": False, "pid": None, "process_started_at": None},
    "dgm_mat": {"enabled": True, "pid": None, "process_started_at": None, "mode": "observer"},
    "kilo": {"enabled": False, "pid": None, "process_started_at": None},
    "llm7": {"enabled": False, "pid": None, "process_started_at": None},
}

app = FastAPI(title="DGM-HUB MultiChat", version="0.3.0")
TASKS: dict[str, dict[str, Any]] = EVENT_STORE.load_tasks()
EVENT_STORE.recover_incomplete_tasks()
TASKS = EVENT_STORE.load_tasks()
ACTIVE_PROCESSES: dict[str, set[subprocess.Popen]] = {name: set() for name in DEFAULT_STATE}
CLAUDE_CLI_VERIFIED = False


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    targets: list[str] = Field(default_factory=lambda: ["codex", "dgm_mat"])
    model: str = OLLAMA_MODEL
    conversation_id: str | None = Field(default=None, min_length=1, max_length=128)
    workspace: str | None = None


class DgmMatModeRequest(BaseModel):
    mode: Literal["observer", "respond", "hybrid"]

    model_config = ConfigDict(extra="forbid")


def load_state() -> dict[str, dict[str, Any]]:
    state = json.loads(json.dumps(DEFAULT_STATE))
    try:
        saved = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        for name in state:
            if name in saved:
                state[name].update(saved[name])
    except (OSError, json.JSONDecodeError):
        pass
    return state


PROVIDERS = load_state()


def save_state() -> None:
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(PROVIDERS, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(STATE_FILE)


def journal(event: dict[str, Any]) -> dict[str, Any]:
    """Append an event with a stable ID and durable sequence number."""
    return EVENT_STORE.append(event)


def safe_workspace(value: str | None) -> Path:
    allowed = ROOT.resolve()
    requested = Path(value).resolve() if value else allowed
    if requested != allowed and allowed not in requested.parents:
        raise HTTPException(403, "Nesta versão, o workspace está limitado à pasta isolada do DGM-HUB.")
    return requested


def http_online(url: str) -> bool:
    try:
        return requests.get(url, timeout=1.5).ok
    except requests.RequestException:
        return False


def _dgm_mat_session_token() -> str:
    with _DGM_MAT_LOCK:
        token = _DGM_MAT_SESSION.get("token")
        if isinstance(token, str) and token and time.monotonic() < float(_DGM_MAT_SESSION.get("expires_at", 0)):
            return token

        configured_path = os.getenv("DGM_LOCAL_BOOTSTRAP_FILE", "").strip()
        if configured_path:
            bootstrap_path = Path(configured_path)
        else:
            local_app_data = Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
            bootstrap_path = local_app_data / "DGM-MAT" / "security" / "bootstrap.token"
        try:
            bootstrap = bootstrap_path.read_text(encoding="utf-8")
        except OSError:
            raise RuntimeError("DGM-MAT local bootstrap credential is unavailable; no request was sent.") from None
        if len(bootstrap) < 60 or bootstrap != bootstrap.strip():
            raise RuntimeError("DGM-MAT local bootstrap credential is invalid; no request was sent.")

        try:
            response = requests.post(
                DGM_MAT_BASE_URL + "/auth/session",
                headers={"Authorization": "Bearer " + bootstrap},
                json={"client_id": "dgm-hub-multichat"},
                timeout=(2, 5),
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"DGM-MAT local session could not be issued ({type(exc).__name__}).") from None
        if response.status_code != 201:
            raise RuntimeError(f"DGM-MAT local session was refused (HTTP {response.status_code}).")
        try:
            payload = response.json()
        except ValueError:
            raise RuntimeError("DGM-MAT local session returned invalid JSON.") from None
        token = payload.get("access_token") if isinstance(payload, dict) else None
        expires_in = payload.get("expires_in", 0) if isinstance(payload, dict) else 0
        if not isinstance(token, str) or not token or not isinstance(expires_in, (int, float)) or expires_in <= 0:
            raise RuntimeError("DGM-MAT local session response was incomplete.")
        _DGM_MAT_SESSION["token"] = token
        _DGM_MAT_SESSION["expires_at"] = time.monotonic() + max(15, float(expires_in) - 60)
        return token


def _dgm_mat_api_request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    token = _dgm_mat_session_token()
    try:
        response = requests.request(
            method,
            DGM_MAT_BASE_URL + path,
            headers={"Authorization": "Bearer " + token},
            json=payload,
            timeout=(3, 45),
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"DGM-MAT API request failed ({type(exc).__name__}); no automatic retry was attempted.") from None
    if response.status_code == 401:
        with _DGM_MAT_LOCK:
            _DGM_MAT_SESSION.update({"token": None, "expires_at": 0.0})
    if not 200 <= response.status_code < 300:
        raise RuntimeError(f"DGM-MAT API returned HTTP {response.status_code} for {path}; no automatic retry was attempted.")
    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(f"DGM-MAT API returned invalid JSON for {path}.") from None
    if not isinstance(result, dict):
        raise RuntimeError(f"DGM-MAT API returned an unexpected response for {path}.")
    return result


def _set_dgm_mat_observer(active: bool) -> dict[str, Any]:
    action = "start" if active else "stop"
    path = f"/governance/agents/hub/observer/{action}"
    try:
        return _dgm_mat_api_request("POST", path)
    except RuntimeError as exc:
        # Older installed DGM-MAT runtimes predate the passive observer API.
        # A 404 proves that no such background observer route is installed;
        # the Hub's own observer/respond mode remains authoritative meanwhile.
        if "HTTP 404" in str(exc):
            return {
                "status": "not_installed",
                "observer_enabled": False,
                "requested_enabled": active,
                "reason": "DGM-MAT passive observer API is not deployed in this runtime.",
            }
        raise


def _valid_dgm_mat_thread_id(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"thread-[0-9a-f]{16}", value) is not None


def _load_dgm_mat_thread_map() -> dict[str, str]:
    try:
        payload = json.loads(DGM_MAT_THREAD_MAP_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        key: value for key, value in payload.items()
        if isinstance(key, str) and _valid_dgm_mat_thread_id(value)
    }


def _save_dgm_mat_thread_map(mapping: dict[str, str]) -> None:
    DGM_MAT_THREAD_MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DGM_MAT_THREAD_MAP_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(DGM_MAT_THREAD_MAP_FILE)


def _dgm_mat_thread_id(conversation_id: str) -> str:
    with _DGM_MAT_LOCK:
        mapping = _load_dgm_mat_thread_map()
        existing = mapping.get(conversation_id)
        if existing:
            return existing
        created = _dgm_mat_api_request(
            "POST",
            "/mobile/threads",
            {"title": "DGM-HUB " + conversation_id[:24], "project": "DGM-MAT"},
        )
        thread_id = created.get("id")
        if not _valid_dgm_mat_thread_id(thread_id):
            raise RuntimeError("DGM-MAT did not return a valid conversation thread ID.")
        mapping[conversation_id] = thread_id
        while len(mapping) > 1000:
            mapping.pop(next(iter(mapping)))
        _save_dgm_mat_thread_map(mapping)
        return thread_id


def process_alive(pid: Any) -> bool:
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_hidden(executable: Path, args: list[str], cwd: Path, stdout_path: Path, stderr_path: Path) -> int:
    if not executable.is_file():
        raise RuntimeError(f"Executável não encontrado: {executable}")
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    out = stdout_path.open("a", encoding="utf-8")
    err = stderr_path.open("a", encoding="utf-8")
    try:
        process = subprocess.Popen(
            [str(executable), *args],
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=err,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    finally:
        out.close()
        err.close()
    return process.pid


def mark_owned_process(entry: dict[str, Any], pid: int) -> None:
    """Persist both PID and creation time to detect PID reuse after restart."""
    entry["pid"] = pid
    try:
        entry["process_started_at"] = psutil.Process(pid).create_time()
    except (psutil.Error, OSError):
        entry["process_started_at"] = None


def stop_owned_process(
    pid: Any,
    expected_executable: Path,
    expected_create_time: Any = None,
    command_pattern: str | None = None,
) -> bool:
    # Never terminate a process based on PID alone. Persisted PIDs may be reused.
    if (
        not isinstance(pid, int)
        or pid <= 0
        or not isinstance(expected_create_time, (int, float))
        or not expected_executable.is_file()
    ):
        return False
    try:
        process = psutil.Process(pid)
        actual = os.path.normcase(os.path.abspath(process.exe()))
        expected = os.path.normcase(os.path.abspath(str(expected_executable)))
        if actual != expected:
            return False
        if abs(process.create_time() - float(expected_create_time)) > 1.0:
            return False
        if command_pattern:
            command = " ".join(process.cmdline())
            if command_pattern.casefold() not in command.casefold():
                return False
        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True, text=True, timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0
    except (psutil.Error, OSError, subprocess.SubprocessError):
        return False


def stop_active_process(process: subprocess.Popen) -> bool:
    # Popen handles belong to this live Hub process, so poll() prevents stale-PID kills.
    if process.poll() is not None:
        return False
    try:
        result = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True, text=True, timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0
    except Exception:
        return False


def start_provider(name: str) -> dict[str, Any]:
    if name not in PROVIDERS:
        raise HTTPException(404, "Provider desconhecido.")
    entry = PROVIDERS[name]
    if name == "codex":
        if not Path(CODEX_CMD).is_file():
            raise HTTPException(503, f"Launcher Codex não encontrado: {CODEX_CMD}")
        entry["enabled"] = True
        save_state()
        return {"provider": name, "enabled": True, "running": True, "message": "Codex Free pronto. O processo CLI arranca quando enviares uma mensagem."}

    if name == "claude":
        if not CLAUDE_EXE.is_file():
            raise HTTPException(503, f"fcc-claude não encontrado: {CLAUDE_EXE}")
        if not http_online(FCC_HEALTH):
            pid = start_hidden(
                FCC_SERVER_EXE, [], Path.home(),
                DATA_DIR / "logs" / "fcc.stdout.log",
                DATA_DIR / "logs" / "fcc.stderr.log",
            )
            mark_owned_process(entry, pid)
            ready = False
            for _ in range(20):
                if http_online(FCC_HEALTH):
                    ready = True
                    break
                time.sleep(0.5)
            if not ready:
                stop_owned_process(pid, FCC_SERVER_EXE, entry.get("process_started_at"))
                entry["pid"] = None
                entry["process_started_at"] = None
                raise HTTPException(503, "FCC Server não abriu o painel admin em 10 segundos. Consulta runtime/multichat/logs/fcc.stderr.log.")
        entry["enabled"] = True
        save_state()
        return {"provider": name, "enabled": True, "running": True, "message": "FCC ativo. Claude CLI pronto para respostas isoladas, apenas de leitura."}

    if name == "ollama":
        if http_online(f"{OLLAMA_URL}/api/tags"):
            entry["enabled"] = True
            save_state()
            return {"provider": name, "enabled": True, "running": True, "message": "Ollama já estava ativo; o Hub não assumiu a propriedade do processo."}
        executable = Path(shutil.which("ollama") or "")
        if not executable.is_file():
            raise HTTPException(503, "Não encontrei o executável Ollama no PATH.")
        pid = start_hidden(
            executable, ["serve"], Path.home(),
            DATA_DIR / "logs" / "ollama.stdout.log",
            DATA_DIR / "logs" / "ollama.stderr.log",
        )
        mark_owned_process(entry, pid)
        ready = False
        for _ in range(30):
            if http_online(f"{OLLAMA_URL}/api/tags"):
                ready = True
                break
            time.sleep(0.5)
        if not ready:
            stop_owned_process(pid, executable, entry.get("process_started_at"))
            entry["pid"] = None
            raise HTTPException(503, "Ollama não ficou pronto em 15 segundos.")
        entry["enabled"] = True
        save_state()
        return {"provider": name, "enabled": True, "running": True, "message": "Ollama iniciado pelo DGM-HUB."}

    if name == "dgm_mat":
        if not http_online(DGM_MAT_HEALTH):
            main_file = DGM_MAT_ROOT / "main.py"
            if not main_file.is_file():
                raise HTTPException(503, "Não encontrei o runtime principal do DGM-MAT.")
            python_exe = Path(shutil.which("python") or "")
            pid = start_hidden(
                python_exe, [str(main_file), "--headless"], DGM_MAT_ROOT,
                DATA_DIR / "logs" / "dgm-mat.stdout.log",
                DATA_DIR / "logs" / "dgm-mat.stderr.log",
            )
            mark_owned_process(entry, pid)
            ready = False
            for _ in range(20):
                if http_online(DGM_MAT_HEALTH):
                    ready = True
                    break
                time.sleep(0.5)
            if not ready:
                stop_owned_process(pid, python_exe, entry.get("process_started_at"))
                entry["pid"] = None
                entry["process_started_at"] = None
                raise HTTPException(503, "DGM-MAT não ficou saudável em 10 segundos.")
        mode = entry.get("mode", "observer")
        if mode == "respond":
            try:
                _set_dgm_mat_observer(False)
            except RuntimeError as exc:
                raise HTTPException(503, f"Não foi possível desativar o observador do DGM-MAT: {exc}") from exc
        entry["enabled"] = True
        save_state()
        labels = {
            "observer": "observa e regista; não responde",
            "respond": "responde através do runtime autenticado do DGM-MAT; observador desligado",
            "hybrid": "observa e responde através do runtime autenticado do DGM-MAT",
        }
        return {"provider": name, "enabled": True, "running": True, "mode": mode, "message": "DGM-MAT ativo: " + labels.get(mode, labels["observer"]) + "."}
    if name in ("kilo", "llm7"):
        base = KILO_URL if name == "kilo" else LLM7_URL
        if not http_online(base + "/models"):
            raise HTTPException(503, f"{name} API n?o respondeu ao endpoint /models.")
        entry["enabled"] = True
        save_state()
        model = KILO_MODEL if name == "kilo" else LLM7_MODEL
        return {"provider": name, "enabled": True, "running": True, "message": f"API gratuita sem chave validada; modelo predefinido: {model}."}
    raise HTTPException(400, "Ação não suportada.")


def stop_provider(name: str) -> dict[str, Any]:
    if name not in PROVIDERS:
        raise HTTPException(404, "Provider desconhecido.")
    entry = PROVIDERS[name]
    entry["enabled"] = False
    message = "Participação desativada."
    active = list(ACTIVE_PROCESSES.get(name, set()))
    for active_process in active:
        stop_active_process(active_process)
    ACTIVE_PROCESSES.get(name, set()).clear()
    if name == "ollama":
        owned_pid = entry.get("pid")
        stopped = False
        if isinstance(owned_pid, int):
            ollama_exe = Path(shutil.which("ollama") or "")
            stopped = stop_owned_process(
                owned_pid,
                ollama_exe,
                entry.get("process_started_at"),
                command_pattern="serve",
            )
        ollama_still_online = http_online(f"{OLLAMA_URL}/api/tags")
        if not ollama_still_online:
            message = "Ollama desligado."
        elif owned_pid is None:
            message = "Participação desativada; Ollama já existente não foi terminado pelo Hub."
        elif stopped:
            message = "Processo Ollama iniciado pelo Hub terminado."
        else:
            message = "Participação desativada; a verificação de propriedade falhou e o processo foi preservado."
        entry["pid"] = None
        entry["process_started_at"] = None
    elif name == "claude":
        owned_pid = entry.get("pid")
        stopped = False
        if isinstance(owned_pid, int):
            stopped = stop_owned_process(
                owned_pid,
                FCC_SERVER_EXE,
                entry.get("process_started_at"),
            )
        fcc_still_online = http_online(FCC_HEALTH)
        if not fcc_still_online:
            message = "Claude/FCC desligado."
        elif owned_pid is None:
            message = "Participação desativada; FCC já existente não foi terminado pelo Hub."
        elif stopped:
            message = "Processo FCC iniciado pelo Hub terminado."
        else:
            message = "Participação desativada; a verificação de propriedade falhou e o FCC foi preservado."
        entry["pid"] = None
        entry["process_started_at"] = None
    elif name == "codex":
        message = "Codex desativado no Hub; não serão iniciadas novas sessões."
    elif name == "dgm_mat":
        message = "DGM-MAT deixou de participar nas conversas. O runtime central permanece ligado para não interromper outros serviços."
    save_state()
    return {"provider": name, "enabled": False, "message": message}


def provider_status() -> dict[str, Any]:
    codex_ok = Path(CODEX_CMD).is_file()
    claude_ok = CLAUDE_EXE.is_file()
    ollama_online = http_online(f"{OLLAMA_URL}/api/tags")
    dgm_online = http_online(DGM_MAT_HEALTH)
    fcc_online = http_online(FCC_HEALTH)
    values = {
        "codex": {"online": codex_ok, "installed": codex_ok, "description": "CLI por mensagem"},
        "claude": {"online": fcc_online, "installed": claude_ok, "fcc_online": fcc_online, "cli_status": "response_verified" if CLAUDE_CLI_VERIFIED else "response_not_yet_verified", "description": "Claude Code via FCC; execucao isolada e somente de leitura"},
        "ollama": {"online": ollama_online, "installed": bool(shutil.which("ollama")), "models": []},
        "dgm_mat": {
            "online": dgm_online,
            "installed": DGM_MAT_ROOT.exists(),
            "mode": str(PROVIDERS["dgm_mat"].get("mode", "observer")),
            "description": "Runtime central DGM-MAT; modo selecionável no painel",
        },
        "kilo": {"online": http_online(KILO_URL + "/models"), "installed": True, "description": "Kilo Gateway ? gratuito sem chave ? openrouter/free"},
        "llm7": {"online": http_online(LLM7_URL + "/models"), "installed": True, "description": "LLM7 ? acesso an?nimo sem chave ? gpt-oss:20b"},
    }
    if ollama_online:
        try:
            values["ollama"]["models"] = [m.get("name") for m in requests.get(f"{OLLAMA_URL}/api/tags", timeout=2).json().get("models", [])]
        except requests.RequestException:
            pass
    for name, item in values.items():
        item["enabled"] = bool(PROVIDERS[name]["enabled"])
        item["ready"] = bool(item["online"] and item["enabled"])
    return {"hub": "online", "providers": values, "dgm_mat_mode": str(PROVIDERS["dgm_mat"].get("mode", "observer"))}


def run_ollama(prompt: str, model: str) -> dict[str, Any]:
    started = time.perf_counter()
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 2048, "num_predict": 192},
        },
        timeout=(4, 75),
    )
    response.raise_for_status()
    data = response.json()
    return {"provider": "ollama", "model": model, "text": data.get("message", {}).get("content", ""), "duration_seconds": round(time.perf_counter() - started, 2), "status": "ok"}


def run_cli(command: list[str], prompt: str, cwd: Path, provider: str, timeout: int = 150, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", cwd=str(cwd), env=env or os.environ.copy(),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    ACTIVE_PROCESSES.setdefault(provider, set()).add(process)
    try:
        try:
            output, errors = process.communicate(input=prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            stop_active_process(process)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            raise
    finally:
        ACTIVE_PROCESSES.setdefault(provider, set()).discard(process)
    output = (output or "").strip()
    errors = (errors or "").strip()
    if process.returncode != 0:
        raise RuntimeError(f"exit={process.returncode}; {errors[-2500:] or output[-2500:]}")
    return {"provider": provider, "text": output or "(O agente terminou sem devolver texto.)", "duration_seconds": round(time.perf_counter() - started, 2), "status": "ok"}


def run_anonymous_api(provider: str, base_url: str, model: str, prompt: str) -> dict[str, Any]:
    started = time.perf_counter()
    # Anonymous endpoints: no API key or local credential is sent.
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 2048, "stream": False}
    if provider == "kilo":
        # The free router can select reasoning models; low effort leaves room for a visible final answer.
        payload["reasoning_effort"] = "low"
    response = requests.post(
        base_url + "/chat/completions",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=(8, 120),
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    message = (choices[0].get("message") or {}) if choices else {}
    content = message.get("content")
    if isinstance(content, list):
        content = "\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    content = str(content or "").strip()
    if not content:
        finish = choices[0].get("finish_reason") if choices else "no_choices"
        raise RuntimeError(f"{provider} n?o devolveu texto (finish_reason={finish}).")
    return {"provider": provider, "model": data.get("model", model), "text": content, "duration_seconds": round(time.perf_counter() - started, 2), "status": "ok"}


def make_prompt(message: str, conversation_id: str, provider: str) -> str:
    return (
        "És um agente independente no DGM-HUB. Responde em Português de Portugal. "
        "Analisa o pedido por mérito próprio; não inventes testes nem alterações feitas. "
        "Se for engenharia, apresenta diagnóstico, proposta, riscos e validação. "
        "Não alteres ficheiros nesta conversa: modo consultivo. "
        f"Conversa: {conversation_id}. Papel: {provider}.\n\nPEDIDO DO ANDRÉ:\n{message}"
    )


def run_codex(prompt: str, cwd: Path) -> dict[str, Any]:
    if not Path(CODEX_CMD).is_file():
        raise RuntimeError(f"Launcher Codex Free não encontrado: {CODEX_CMD}")
    return run_cli(["cmd.exe", "/d", "/c", CODEX_CMD, "exec", "--skip-git-repo-check", "-"], prompt, cwd, "codex", timeout=75)


def run_claude(prompt: str, cwd: Path) -> dict[str, Any]:
    global CLAUDE_CLI_VERIFIED
    if not http_online(FCC_HEALTH):
        raise RuntimeError("FCC Server is not active. Enable Claude in the provider panel.")
    if not CLAUDE_NODE_EXE.is_file() or not CLAUDE_CLI_JS.is_file():
        raise RuntimeError(f"Claude Code CLI not found: {CLAUDE_CLI_JS}")
    CLAUDE_MCP_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if not CLAUDE_MCP_CONFIG.is_file():
        CLAUDE_MCP_CONFIG.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    claude_env = os.environ.copy()
    claude_env.update({
        "ANTHROPIC_BASE_URL": "http://127.0.0.1:8082",
        "ANTHROPIC_AUTH_TOKEN": "freecc",
        "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "190000",
        "DISABLE_AUTOUPDATER": "1",
        "CI": "1",
        "TERM": "dumb",
    })
    command = [
        str(CLAUDE_NODE_EXE), str(CLAUDE_CLI_JS), "-p", prompt,
        "--strict-mcp-config", "--mcp-config", str(CLAUDE_MCP_CONFIG),
        "--no-session-persistence", "--output-format", "text",
        "--permission-mode", "plan",
    ]
    result = run_cli(command, "", cwd, "claude", timeout=180, env=claude_env)
    CLAUDE_CLI_VERIFIED = True
    return result


def run_dgm_observer(message: str, conversation_id: str, task_id: str) -> dict[str, Any]:
    online = http_online(DGM_MAT_HEALTH)
    journal({
        "kind": "dgm_mat_observation",
        "task_id": task_id,
        "conversation_id": conversation_id,
        "user_message": message,
        "mode": "observer",
    })
    text = (
        "Estou presente como observador do DGM-MAT. Registei o pedido para análise e aprendizagem. "
        f"Runtime {'saudável' if online else 'indisponível'}. "
        "A decisão e a liderança continuam exclusivamente contigo."
    )
    return {"provider": "dgm_mat", "text": text, "duration_seconds": 0, "status": "observer"}


def run_dgm_mat_responder(message: str, conversation_id: str, task_id: str) -> dict[str, Any]:
    if not http_online(DGM_MAT_HEALTH):
        raise RuntimeError("DGM-MAT não está saudável; a mensagem não foi encaminhada.")
    thread_id = _dgm_mat_thread_id(conversation_id)
    try:
        response = _dgm_mat_api_request(
            "POST",
            f"/mobile/threads/{thread_id}/messages",
            {"content": message},
        )
    except RuntimeError as exc:
        if "HTTP 404" not in str(exc):
            raise
        with _DGM_MAT_LOCK:
            mapping = _load_dgm_mat_thread_map()
            mapping.pop(conversation_id, None)
            _save_dgm_mat_thread_map(mapping)
        thread_id = _dgm_mat_thread_id(conversation_id)
        response = _dgm_mat_api_request(
            "POST",
            f"/mobile/threads/{thread_id}/messages",
            {"content": message},
        )

    answer = response.get("message")
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("DGM-MAT não devolveu uma resposta de conversa válida.")
    intent = response.get("intent") if isinstance(response.get("intent"), dict) else {}
    return {
        "provider": "dgm_mat",
        "status": "ok",
        "text": answer[:12000],
        "duration_seconds": 0,
        "mode": "respond",
        "thread_id": thread_id,
        "mission_id": response.get("mission_id"),
        "intent": intent,
        "response_source": "authenticated_dgm_mat_mobile_runtime",
    }


def run_dgm_mat(message: str, conversation_id: str, task_id: str) -> dict[str, Any]:
    mode = str(PROVIDERS["dgm_mat"].get("mode", "observer"))
    if mode == "observer":
        return run_dgm_observer(message, conversation_id, task_id)
    if mode == "respond":
        return run_dgm_mat_responder(message, conversation_id, task_id)
    if mode == "hybrid":
        observed = run_dgm_observer(message, conversation_id, task_id)
        response = run_dgm_mat_responder(message, conversation_id, task_id)
        response["mode"] = "hybrid"
        response["observation_recorded"] = observed.get("status") == "observer"
        return response
    raise RuntimeError("Modo DGM-MAT desconhecido; pedido recusado.")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return HTML_FILE.read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return provider_status()


@app.get("/api/providers")
def providers() -> dict[str, Any]:
    return provider_status()


@app.post("/api/providers/{name}/start")
def provider_start(name: str) -> dict[str, Any]:
    return start_provider(name)


@app.post("/api/providers/{name}/stop")
def provider_stop(name: str) -> dict[str, Any]:
    return stop_provider(name)


@app.post("/api/providers/dgm_mat/mode")
def set_dgm_mat_mode(request: DgmMatModeRequest) -> dict[str, Any]:
    """Change DGM-MAT participation mode and synchronize its passive observer."""
    active_observer = request.mode in {"observer", "hybrid"}
    try:
        observer_state = _set_dgm_mat_observer(active_observer)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"Modo não alterado; controlo do observador falhou: {exc}") from exc
    PROVIDERS["dgm_mat"]["mode"] = request.mode
    save_state()
    passive_observer_enabled = (
        False if observer_state.get("status") == "not_installed" else active_observer
    )
    messages = {
        "observer": "O DGM-MAT observa e regista; não responde na sala.",
        "respond": "O observador foi desligado. O DGM-MAT responde através da sua API local autenticada.",
        "hybrid": "O DGM-MAT observa e também responde através da sua API local autenticada.",
    }
    message = messages[request.mode]
    if observer_state.get("status") == "not_installed":
        message += " A captura passiva adicional ainda não está instalada neste runtime; o registo por pedido funciona quando o DGM-MAT está selecionado."
    return {
        "provider": "dgm_mat",
        "mode": request.mode,
        "observer_enabled": passive_observer_enabled,
        "observer_state": observer_state,
        "message": message,
    }


async def execute_provider(task_id: str, conversation_id: str, name: str, job: Any) -> None:
    task = TASKS[task_id]
    task["status"] = "running"
    TASKS[task_id] = EVENT_STORE.save_task(task)
    try:
        result = await asyncio.to_thread(job)
    except subprocess.TimeoutExpired:
        result = {"provider": name, "status": "timeout", "text": "Tempo limite excedido."}
    except Exception as exc:
        result = {"provider": name, "status": "error", "text": f"{type(exc).__name__}: {str(exc)[:2500]}"}

    result.setdefault("provider", name)
    task = TASKS[task_id]
    task["results"][name] = result
    if name not in task["completed"]:
        task["completed"].append(name)
    if len(task["completed"]) >= len(task["targets"]):
        successful = sum(
            1 for item in task["results"].values()
            if item.get("status") in {"ok", "observer"}
        )
        if successful == len(task["targets"]):
            task["status"] = "completed"
        elif successful:
            task["status"] = "partial"
        else:
            task["status"] = "failed"
    else:
        task["status"] = "running"

    event_kind = (
        "provider_response"
        if result.get("status") in {"ok", "observer"}
        else "provider_error"
    )
    stored_task, _event = EVENT_STORE.save_task_and_event(
        task,
        {
            "kind": event_kind,
            "task_id": task_id,
            "conversation_id": conversation_id,
            **result,
        },
    )
    TASKS[task_id] = stored_task


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    message = request.message.strip()
    if not message:
        raise HTTPException(400, "A mensagem não pode estar vazia.")
    targets = list(dict.fromkeys(request.targets))
    if not targets or any(target not in PROVIDERS for target in targets):
        raise HTTPException(400, "Seleciona pelo menos um provider válido.")
    disabled = [name for name in targets if not PROVIDERS[name]["enabled"]]
    if disabled:
        raise HTTPException(409, "Providers desligados: " + ", ".join(disabled) + ". Liga-os no painel antes de enviar.")
    conversation_id = request.conversation_id or str(uuid.uuid4())
    workspace = safe_workspace(request.workspace)
    prompt = make_prompt(message, conversation_id, "consultor")
    task_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    task = {
        "task_id": task_id,
        "conversation_id": conversation_id,
        "targets": targets,
        "completed": [],
        "results": {},
        "created_at": created_at,
        "updated_at": created_at,
        "status": "queued",
    }
    TASKS[task_id] = task
    EVENT_STORE.create_task(
        task,
        {
            "kind": "user_message",
            "task_id": task_id,
            "conversation_id": conversation_id,
            "message": message,
            "targets": targets,
            "workspace": str(workspace),
        },
    )
    jobs = {
        "ollama": lambda: run_ollama(prompt, request.model),
        "codex": lambda: run_codex(prompt, workspace),
        "claude": lambda: run_claude(prompt, workspace),
        "dgm_mat": lambda: run_dgm_mat(message, conversation_id, task_id),
        "kilo": lambda: run_anonymous_api("kilo", KILO_URL, KILO_MODEL, prompt),
        "llm7": lambda: run_anonymous_api("llm7", LLM7_URL, LLM7_MODEL, prompt),
    }
    for name in targets:
        asyncio.create_task(execute_provider(task_id, conversation_id, name, jobs[name]))
    return {"task_id": task_id, "conversation_id": conversation_id, "targets": targets}


@app.get("/api/tasks/{task_id}")
def task_status(task_id: str) -> dict[str, Any]:
    task = TASKS.get(task_id) or EVENT_STORE.get_task(task_id)
    if not task:
        raise HTTPException(404, "Tarefa não encontrada.")
    TASKS[task_id] = task
    terminal = task.get("status") in {"completed", "partial", "failed", "interrupted"}
    return {
        "task_id": task_id,
        "conversation_id": task["conversation_id"],
        "targets": task["targets"],
        "completed": task["completed"],
        "results": task["results"],
        "status": task.get("status", "unknown"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at"),
        "done": terminal or len(task["completed"]) == len(task["targets"]),
    }


@app.get("/api/history")
def history(
    limit: int = Query(default=100, ge=1, le=500),
    after: str | None = None,
) -> dict[str, Any]:
    try:
        return EVENT_STORE.page(after=after, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
