import json
from pathlib import Path

from core.lexicon_promotion_contract import (
    APPROVED_FOR_RUNTIME,
    REQUIRED_REGRESSION_KINDS,
    LexiconPromotionCandidate,
    runtime_promotion_blockers,
    runtime_promotion_ready,
)
from core.safety_corpus_review import safety_corpus_fingerprint
from core.triage_classification import glycemic_emergency_variant_inventory

_FIXTURE = Path(__file__).parent / "fixtures" / "darija_lexicon_batch03_adversarial.json"


def _candidate(**overrides):
    payload = {
        "candidate_id": "test-darija-candidate-01",
        "locale": "ar-MA",
        "phrase": "synthetic reviewed phrase",
        "channel": "text",
        "input_form": "latin_transliteration",
        "source_evidence_reference": "test/source/batch03",
        "safety_corpus_fingerprint": safety_corpus_fingerprint(),
        "native_review_reference": "test/native/review",
        "clinical_review_reference": "test/clinical/review",
        "safety_owner_review_reference": "test/safety-owner/review",
        "parity_review_reference": "test/parity/review",
        "regression_kinds": REQUIRED_REGRESSION_KINDS,
        "decision": APPROVED_FOR_RUNTIME,
    }
    payload.update(overrides)
    return LexiconPromotionCandidate(**payload)


def test_batch03_adversarial_fixture_is_explicitly_non_runtime():
    cases = json.loads(_FIXTURE.read_text(encoding="utf-8"))

    assert cases
    assert all(case["runtime_authorized"] is False for case in cases)
    assert {case["category"] for case in cases} >= {
        "hyperbole",
        "ambiguity",
        "device_reading",
        "device_symptom_discordance",
        "device_failure",
        "medication_event",
        "medication_uncertainty",
    }
    assert all(case["semantic_boundary"].strip() for case in cases)


def test_batch03_fixture_does_not_silently_enter_runtime_variant_inventory():
    fixture_texts = {
        case["text"] for case in json.loads(_FIXTURE.read_text(encoding="utf-8"))
    }
    runtime_texts = {variant.text for variant in glycemic_emergency_variant_inventory()}

    assert fixture_texts.isdisjoint(runtime_texts)


def test_promotion_fails_closed_when_restricted_review_evidence_is_missing():
    candidate = _candidate(
        native_review_reference="",
        clinical_review_reference="",
        safety_owner_review_reference="",
        parity_review_reference="",
        decision="working_evidence_only",
    )

    blockers = runtime_promotion_blockers(candidate)

    assert "native_review:missing_or_invalid" in blockers
    assert "clinical_review:missing_or_invalid" in blockers
    assert "safety_owner_review:missing_or_invalid" in blockers
    assert "parity_review:missing_or_invalid" in blockers
    assert "decision:not_approved:working_evidence_only" in blockers
    assert not runtime_promotion_ready(candidate)


def test_promotion_requires_all_adversarial_regression_classes():
    candidate = _candidate(regression_kinds=frozenset({"positive", "negative"}))

    blockers = runtime_promotion_blockers(candidate)

    assert "regression:missing:contextual" in blockers
    assert "regression:missing:hyperbole" in blockers
    assert "regression:missing:ambiguity" in blockers
    assert not runtime_promotion_ready(candidate)


def test_promotion_rejects_stale_safety_corpus_fingerprint():
    candidate = _candidate(safety_corpus_fingerprint="0" * 64)

    assert "safety_corpus:fingerprint_mismatch" in runtime_promotion_blockers(candidate)
    assert not runtime_promotion_ready(candidate)


def test_channel_and_input_form_are_validated_independently():
    bad_channel = _candidate(channel="latin_transliteration")
    bad_input_form = _candidate(input_form="voice_transcript")

    assert "channel:unsupported:latin_transliteration" in runtime_promotion_blockers(
        bad_channel
    )
    assert "input_form:unsupported:voice_transcript" in runtime_promotion_blockers(
        bad_input_form
    )


def test_contract_can_only_report_ready_when_every_gate_is_present():
    candidate = _candidate()

    assert runtime_promotion_blockers(candidate) == ()
    assert runtime_promotion_ready(candidate)
