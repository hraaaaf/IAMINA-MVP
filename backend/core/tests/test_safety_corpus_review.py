import json
import stat
from copy import deepcopy
from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.safety_corpora import (
    HIGH_SEVERITY_VARIANT_CASES,
    all_safety_corpus_cases,
)
from core.safety_corpus_review import (
    SCHEMA_VERSION,
    load_safety_review_manifest,
    native_review_readiness_payload,
    required_parity_dimensions,
    safety_corpus_fingerprint,
    safety_corpus_packet_payload,
    write_safety_corpus_packet,
)
from core.triage_classification import (
    TriageClass,
    classify,
    glycemic_emergency_variant_inventory,
)

TODAY = date(2026, 8, 4)
SOURCE_SHA = "0ed679f232e640b8300e8fea20e0a08958d71baf"


def _approved_manifest():
    packet = safety_corpus_packet_payload()
    return {
        "schema_version": SCHEMA_VERSION,
        "corpus_fingerprint": packet["corpus_fingerprint"],
        "source_commit_sha": SOURCE_SHA,
        "review_batch_reference": "NATIVE-REVIEW-BATCH-2026-08",
        "clinical_approval_reference": "CLINICAL-APPROVAL-2026-08",
        "safety_owner_approval_reference": "SAFETY-OWNER-APPROVAL-2026-08",
        "reviewed_on": "2026-08-04",
        "review_due_on": "2026-11-04",
        "locale_reviews": [
            {
                "locale": locale,
                "native_reviewer_reference": f"NATIVE-REVIEWER-{locale.replace('-', '_')}",
                "qualification_reference": f"QUALIFICATION-{locale.replace('-', '_')}",
                "decision": "approved",
            }
            for locale in packet["required_locales"]
        ],
        "case_reviews": [
            {
                "case_id": case["case_id"],
                "native_decision": "approved",
                "clinical_decision": "approved",
                "issue_reference": "",
            }
            for case in packet["cases"]
        ],
        "parity_reviews": [
            {
                **dimension,
                "reviewer_reference": (
                    "PARITY-REVIEWER-"
                    f"{dimension['locale'].replace('-', '_')}-"
                    f"{dimension['channel']}-{dimension['input_form']}"
                ),
                "decision": "approved",
            }
            for dimension in packet["required_parity_dimensions"]
        ],
    }


def _write_manifest(tmp_path, payload):
    path = tmp_path / "native-review-manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_every_exact_classifier_variant_is_in_the_review_corpus():
    inventory = {
        (variant.locale, variant.input_form, variant.text)
        for variant in glycemic_emergency_variant_inventory()
    }
    corpus = {
        (case.locale, case.input_form, case.text)
        for case in HIGH_SEVERITY_VARIANT_CASES
    }

    assert corpus == inventory
    assert corpus
    assert all(classify(case.text) is TriageClass.GLYCEMIC_EMERGENCY for case in HIGH_SEVERITY_VARIANT_CASES)


def test_corpus_case_ids_are_unique_and_deterministic():
    cases = all_safety_corpus_cases()
    assert len({case.case_id for case in cases}) == len(cases)
    assert all(case.case_id for case in cases)


def test_packet_covers_baseline_locales_and_required_parity_dimensions():
    packet = safety_corpus_packet_payload()

    assert set(packet["required_locales"]) == {"fr", "ar", "en", "ar-MA"}
    assert packet["case_count"] == len(all_safety_corpus_cases())
    assert {
        (item["locale"], item["channel"], item["input_form"])
        for item in packet["required_parity_dimensions"]
    } == required_parity_dimensions()
    assert ("ar-MA", "voice_transcript", "latin_transliteration") in required_parity_dimensions()
    assert ("ar-MA", "text", "mixed_language") in required_parity_dimensions()
    assert ("ar-MA", "text", "arabic_script") in required_parity_dimensions()


def test_fingerprint_changes_when_reviewable_content_changes():
    packet = safety_corpus_packet_payload()
    modified = deepcopy(packet["cases"])
    modified[0]["text"] += " changed"

    assert safety_corpus_fingerprint(cases=modified) != packet["corpus_fingerprint"]


def test_missing_manifest_is_pending_and_release_gate_fails():
    payload = native_review_readiness_payload(today=TODAY)

    assert payload["status"] == "pending_native_review"
    assert payload["blockers"] == ["restricted_native_review_manifest_missing"]
    with pytest.raises(ValueError, match="not approved"):
        native_review_readiness_payload(today=TODAY, require_approved=True)


def test_complete_approved_manifest_passes(tmp_path):
    path = _write_manifest(tmp_path, _approved_manifest())

    payload = native_review_readiness_payload(
        manifest_path=path,
        today=TODAY,
        require_approved=True,
    )

    assert payload["status"] == "approved"
    assert payload["case_count"] == len(all_safety_corpus_cases())
    assert payload["parity_review_count"] == len(required_parity_dimensions())
    assert payload["blockers"] == []


def test_manifest_must_match_exact_corpus_fingerprint(tmp_path):
    payload = _approved_manifest()
    payload["corpus_fingerprint"] = "0" * 64
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        native_review_readiness_payload(manifest_path=path, today=TODAY)


def test_manifest_must_cover_every_case_exactly(tmp_path):
    payload = _approved_manifest()
    payload["case_reviews"] = payload["case_reviews"][:-1]
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="case coverage incomplete"):
        native_review_readiness_payload(manifest_path=path, today=TODAY)


def test_manifest_must_cover_every_locale(tmp_path):
    payload = _approved_manifest()
    payload["locale_reviews"] = payload["locale_reviews"][:-1]
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="locale coverage incomplete"):
        native_review_readiness_payload(manifest_path=path, today=TODAY)


def test_manifest_must_cover_every_parity_dimension(tmp_path):
    payload = _approved_manifest()
    payload["parity_reviews"] = payload["parity_reviews"][:-1]
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="parity coverage incomplete"):
        native_review_readiness_payload(manifest_path=path, today=TODAY)


def test_rejected_case_blocks_real_pilot_gate(tmp_path):
    payload = _approved_manifest()
    payload["case_reviews"][0]["native_decision"] = "rejected"
    payload["case_reviews"][0]["issue_reference"] = "LINGUISTIC-ISSUE-001"
    path = _write_manifest(tmp_path, payload)

    readiness = native_review_readiness_payload(manifest_path=path, today=TODAY)
    assert readiness["status"] == "review_rejected"
    assert any(":native:rejected" in blocker for blocker in readiness["blockers"])
    with pytest.raises(ValueError, match="not approved"):
        native_review_readiness_payload(
            manifest_path=path,
            today=TODAY,
            require_approved=True,
        )


def test_direct_reviewer_contact_data_is_rejected(tmp_path):
    payload = _approved_manifest()
    payload["locale_reviews"][0]["native_reviewer_reference"] = "reviewer@example.com"
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="opaque evidence reference"):
        native_review_readiness_payload(manifest_path=path, today=TODAY)


def test_stale_manifest_is_rejected(tmp_path):
    payload = _approved_manifest()
    payload["review_due_on"] = "2026-08-03"
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="manifest is stale"):
        native_review_readiness_payload(manifest_path=path, today=TODAY)


def test_packet_export_is_mode_0600_and_fingerprint_stable(tmp_path):
    destination = write_safety_corpus_packet(tmp_path / "review-packet.json")
    exported = json.loads(destination.read_text(encoding="utf-8"))

    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert exported["corpus_fingerprint"] == safety_corpus_packet_payload()["corpus_fingerprint"]


def test_manifest_loader_rejects_unknown_keys(tmp_path):
    payload = _approved_manifest()
    payload["reviewer_name"] = "not allowed"
    path = _write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="keys invalid"):
        load_safety_review_manifest(path)


def test_commands_export_and_fail_closed_without_approval(tmp_path, capsys, monkeypatch):
    output = tmp_path / "packet.json"
    call_command("export_safety_corpus_review_packet", "--output", str(output))
    assert output.exists()
    assert capsys.readouterr().out.strip().endswith("packet.json")

    monkeypatch.delenv("SAFETY_CORPUS_REVIEW_MANIFEST_PATH", raising=False)
    call_command("audit_safety_corpus_review")
    assert '"status": "pending_native_review"' in capsys.readouterr().out
    with pytest.raises(CommandError, match="not approved"):
        call_command("audit_safety_corpus_review", "--require-approved")
