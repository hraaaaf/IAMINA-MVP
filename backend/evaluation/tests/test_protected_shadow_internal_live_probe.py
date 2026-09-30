from pathlib import Path

import pytest

from evaluation import protected_shadow_internal_live_probe as probe


def test_internal_live_probe_is_bounded_and_content_free(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PROTECTED_SHADOW_INTERNAL_LIVE_NETWORK_AUTHORIZED", "true")
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")

    def fake_generate(
        envelope,
        *,
        internal_authorized=False,
        internal_subject_id=None,
    ):
        assert internal_authorized is True
        assert internal_subject_id == 0
        if envelope.locale.script == "arabic":
            wrapper = "أكيد."
        elif envelope.locale.script == "latin":
            wrapper = "Wakha."
        else:
            wrapper = "D'accord."
        return f"{wrapper} {envelope.protected_body_token}"

    monkeypatch.setattr(
        probe,
        "generate_protected_provider_shadow_candidate",
        fake_generate,
    )

    output = tmp_path / "probe.json"
    report = probe.run_probe(output_path=output)

    assert report["machine_passed"] is True
    assert report["planned_calls"] == 3
    assert report["hard_call_ceiling"] == 3
    assert report["patient_data"] is False
    rendered = output.read_text(encoding="utf-8")
    assert "142 mg/dL" not in rendered
    assert "Aide-moi à préparer les questions pour mon médecin." not in rendered
    assert "{{NVB_" not in rendered
    assert all(row["clinical_body_sent"] is False for row in report["results"])
    assert all(row["clinical_value_sent"] is False for row in report["results"])


def test_internal_live_probe_requires_explicit_network_authorization(
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.delenv("PROTECTED_SHADOW_INTERNAL_LIVE_NETWORK_AUTHORIZED", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")

    with pytest.raises(RuntimeError, match="not explicitly authorized"):
        probe.run_probe(output_path=tmp_path / "probe.json")


def test_internal_live_probe_rejects_missing_wrapper(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PROTECTED_SHADOW_INTERNAL_LIVE_NETWORK_AUTHORIZED", "true")
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(
        probe,
        "generate_protected_provider_shadow_candidate",
        lambda envelope, *, internal_authorized=False, internal_subject_id=None: (
            envelope.protected_body_token
        ),
    )

    report = probe.run_probe(output_path=tmp_path / "probe.json")

    assert report["machine_passed"] is False
    assert all("wrapper_missing" in row["violations"] for row in report["results"])
