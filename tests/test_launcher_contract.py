from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_local_launcher_is_loopback_only_and_does_not_start_optional_providers():
    script = (ROOT / "scripts" / "Start-DGM-HUB.ps1").read_text(encoding="utf-8")
    assert "127.0.0.1:8181/health" in script
    assert "127.0.0.1:$Port/api/health/live" in script
    assert "else { 8771 }" in script
    assert "'127.0.0.1'" in script
    assert "installed\\DGM-MAT.exe" in script
    assert "run_multichat:app" in script
    assert "ollama serve" not in script.casefold()
    assert "fcc-server.exe" not in script.casefold()
    assert "Test-PortListener" in script


def test_cmd_launcher_invokes_the_repository_powershell_script():
    command = (ROOT / "Start-DGM-HUB.cmd").read_text(encoding="utf-8")
    assert "scripts\\Start-DGM-HUB.ps1" in command
