from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import run_multichat as hub


def test_project_audit_prompt_declares_no_access_without_evidence():
    prompt = hub.make_prompt(
        "Verifica o estado geral do DGM-MAT e lista erros e correções.",
        "conversation-audit",
        "kilo",
    )

    assert "CONTRATO DE VERACIDADE OBRIGATÓRIO" in prompt
    assert "CONTEXTO DE EVIDÊNCIA: NENHUM" in prompt
    assert "NÃO TENHO EVIDÊNCIA SUFICIENTE" in prompt
    assert "Nunca inventes nomes de ficheiros" in prompt


def test_project_audit_prompt_includes_read_only_evidence_and_citation_rules():
    prompt = hub.make_prompt(
        "Audita o DGM-MAT.",
        "conversation-audit",
        "llm7",
        "[E1] Current branch\nmain",
    )

    assert "[E1] Current branch" in prompt
    assert "Cada afirmação factual" in prompt
    assert "Não inventes referências" in prompt


def test_evidence_collector_uses_allowlisted_files_and_public_pr_metadata(monkeypatch, tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='dgm-mat'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# DGM-MAT\nVerified project README.\n", encoding="utf-8")
    (tmp_path / "docs" / "AUTONOMOUS_RUNTIME.md").write_text("# Runtime\nRead-only evidence.\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (tmp_path / "tests" / "test_runtime.py").write_text("def test_runtime(): pass\n", encoding="utf-8")
    monkeypatch.setattr(hub, "DGM_MAT_ROOT", tmp_path.resolve())
    monkeypatch.setattr(hub, "EVIDENCE_CACHE", {"expires_at": 0.0, "packet": None})

    def fake_run(command, **kwargs):
        args = command[3:]
        if args[:2] == ["rev-parse", "--show-toplevel"]:
            output = str(tmp_path)
        elif args[:2] == ["branch", "--show-current"]:
            output = "feature/evidence-audit"
        elif args[:2] == ["log", "-1"]:
            output = "abc123\n2026-11-05\nEvidence snapshot"
        elif args[:2] == ["remote", "get-url"]:
            output = "https://github.com/AndreVazao/DGM-MAT.git"
        elif args[:2] == ["status", "--short"]:
            output = "## feature/evidence-audit"
        else:
            raise AssertionError(f"Unexpected git command: {command}")
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    class FakeResponse:
        ok = True
        status_code = 200

        @staticmethod
        def json():
            return [{
                "number": 225,
                "title": "Require evidence-grounded audits",
                "draft": True,
                "head": {"ref": "fix/evidence"},
                "updated_at": "2026-11-05T18:00:00Z",
            }]

    monkeypatch.setattr(hub.subprocess, "run", fake_run)
    monkeypatch.setattr(hub.requests, "get", lambda *args, **kwargs: FakeResponse())

    packet = hub.collect_dgm_mat_evidence()

    assert packet["available"] is True
    assert packet["refs"]
    assert packet["sources"][0]["label"] == "Evidence packet scope and limitations"
    assert "does not read the DGM-HUB repository" in packet["text"]
    assert "feature/evidence-audit" in packet["text"]
    assert "pyproject.toml" in packet["text"]
    assert "ci.yml" in packet["text"]
    assert "tests/test_runtime.py" in packet["text"]
    assert "#225 Require evidence-grounded audits" in packet["text"]
    assert "https://github.com/AndreVazao/DGM-MAT.git" in packet["text"]


def test_project_audit_prompt_requires_citations_on_every_content_line():
    prompt = hub.make_prompt(
        "Audita o DGM-MAT.",
        "conversation-audit",
        "codex",
        "[E1] Evidence packet scope\nBounded read-only evidence.",
    )

    assert "cada linha de conteúdo não vazia" in prompt
    assert "recomendações e conclusões" in prompt
    assert "responde apenas com esta linha exata" in prompt


def test_evidence_gate_accepts_explicit_abstention_without_claims():
    task = {"requires_evidence": True, "evidence_refs": ["E1", "E2"]}
    result = {
        "provider": "claude",
        "status": "ok",
        "text": "NÃO TENHO EVIDÊNCIA SUFICIENTE.",
    }

    gated = hub.apply_evidence_gate(result, task)

    assert gated["status"] == "abstained"
    assert gated["grounding_status"] == "abstained_insufficient_evidence"
    assert gated["evidence_refs"] == []
    assert gated["text"] == "NÃO TENHO EVIDÊNCIA SUFICIENTE."


def test_evidence_gate_does_not_allow_claims_after_an_abstention():
    task = {"requires_evidence": True, "evidence_refs": ["E1"]}
    result = {
        "provider": "claude",
        "status": "ok",
        "text": "NÃO TENHO EVIDÊNCIA SUFICIENTE.\nA branch atual é main.",
    }

    gated = hub.apply_evidence_gate(result, task)

    assert gated["status"] == "unverified"
    assert gated["grounding_status"] == "blocked_missing_or_invalid_evidence_citations"


def test_evidence_gate_hides_unreferenced_provider_claims():
    task = {"requires_evidence": True, "evidence_refs": ["E1", "E2"]}
    result = {"provider": "llm7", "status": "ok", "text": "requirements.txt is obsolete."}

    gated = hub.apply_evidence_gate(result, task)

    assert gated["status"] == "unverified"
    assert gated["grounding_status"] == "blocked_missing_or_invalid_evidence_citations"
    assert gated["unverified_text"] == "requirements.txt is obsolete."
    assert "Resposta retida" in gated["text"]


def test_evidence_gate_accepts_only_known_reference_ids():
    task = {"requires_evidence": True, "evidence_refs": ["E1", "E2"]}
    result = {"provider": "kilo", "status": "ok", "text": "A branch foi confirmada [E1]."}

    gated = hub.apply_evidence_gate(result, task)

    assert gated["status"] == "ok"
    assert gated["grounding_status"] == "evidence_citations_present_semantic_review_required"
    assert gated["evidence_refs"] == ["E1"]


def test_evidence_gate_rejects_fabricated_reference_ids():
    task = {"requires_evidence": True, "evidence_refs": ["E1"]}
    result = {"provider": "llm7", "status": "ok", "text": "O teste passou [E9]."}

    gated = hub.apply_evidence_gate(result, task)

    assert gated["status"] == "unverified"
    assert gated["grounding_status"] == "blocked_missing_or_invalid_evidence_citations"


def test_liveness_endpoint_does_not_probe_external_providers(monkeypatch):
    monkeypatch.setattr(
        hub,
        "provider_status",
        lambda: (_ for _ in ()).throw(AssertionError("liveness must not probe providers")),
    )
    response = TestClient(hub.app).get("/api/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "dgm-hub"


def test_evidence_gate_rejects_uncited_claim_even_when_another_line_is_cited():
    task = {"requires_evidence": True, "evidence_refs": ["E1", "E2"]}
    result = {
        "provider": "llm7",
        "status": "ok",
        "text": "A branch atual é main [E1].\nO projeto usa numpy==1.18.5.",
    }

    gated = hub.apply_evidence_gate(result, task)

    assert gated["status"] == "unverified"
    assert gated["grounding_status"] == "blocked_missing_or_invalid_evidence_citations"
    assert "numpy==1.18.5" in gated["unverified_text"]


def test_evidence_gate_rejects_unknown_reference_on_one_line():
    task = {"requires_evidence": True, "evidence_refs": ["E1"]}
    result = {
        "provider": "llm7",
        "status": "ok",
        "text": "A branch é main [E1].\nA dependência está obsoleta [E9].",
    }

    gated = hub.apply_evidence_gate(result, task)

    assert gated["status"] == "unverified"


def test_evidence_collector_does_not_read_project_files_when_origin_is_unconfirmed(monkeypatch, tmp_path: Path):
    (tmp_path / "README.md").write_text("SECRET TEST MARKER", encoding="utf-8")
    monkeypatch.setattr(hub, "DGM_MAT_ROOT", tmp_path.resolve())
    monkeypatch.setattr(hub, "EVIDENCE_CACHE", {"expires_at": 0.0, "packet": None})

    def fake_run(command, **kwargs):
        args = command[3:]
        if args[:2] == ["rev-parse", "--show-toplevel"]:
            output = str(tmp_path)
        elif args[:2] == ["remote", "get-url"]:
            output = "https://github.com/another-owner/another-repo.git"
        else:
            raise AssertionError(f"Project metadata must not be read: {args}")
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(hub.subprocess, "run", fake_run)
    monkeypatch.setattr(hub.requests, "get", lambda *args, **kwargs: SimpleNamespace(ok=False, status_code=503))

    packet = hub.collect_dgm_mat_evidence()

    assert "SECRET TEST MARKER" not in packet["text"]
    assert "not confirmed as AndreVazao/DGM-MAT" in packet["text"]
