import json
import pathlib

_PLAN = pathlib.Path(__file__).parent / "fixtures" / "darija_high_severity_runtime_remediation_plan.json"
_OUTCOMES = pathlib.Path(__file__).parent / "fixtures" / "darija_high_severity_native_review_outcomes.json"


def _plan():
    return json.loads(_PLAN.read_text(encoding="utf-8"))


def _outcomes():
    return json.loads(_OUTCOMES.read_text(encoding="utf-8"))


def _runtime_inventory():
    from core.triage_classification import glycemic_emergency_variant_inventory

    return {
        (variant.input_form, variant.text)
        for variant in glycemic_emergency_variant_inventory()
        if variant.locale == "ar-MA"
    }


def test_remediation_plan_exactly_covers_all_rejected_native_review_outcomes():
    rejected_from_review = {
        (row["input_form"], row["text"])
        for row in _outcomes()
        if row["native_evidence_status"] == "rejected_exact_native_evidence"
    }
    rejected_from_plan = {
        (row["input_form"], row["text"])
        for row in _plan()["rejected_runtime_variants"]
    }

    assert len(rejected_from_review) == 21
    assert rejected_from_plan == rejected_from_review


def test_staging_does_not_silently_change_current_runtime_inventory():
    plan = _plan()
    runtime = _runtime_inventory()
    rejected = {
        (row["input_form"], row["text"])
        for row in plan["rejected_runtime_variants"]
    }
    pending = {
        (row["input_form"], row["runtime_text"])
        for row in plan["pending_replacements"]
    }

    assert plan["runtime_changed"] is False
    assert len(runtime) == 36
    assert rejected <= runtime
    assert pending.isdisjoint(runtime)


def test_all_native_accepted_existing_variants_remain_in_runtime_while_cutover_is_blocked():
    accepted = {
        (row["input_form"], row["text"])
        for row in _outcomes()
        if row["native_evidence_status"] == "accepted_exact_native_evidence"
    }

    assert len(accepted) == 15
    assert accepted <= _runtime_inventory()


def test_pending_replacements_are_fail_closed_and_not_active_classifiers():
    from core.triage_classification import TriageClass, classify

    for row in _plan()["pending_replacements"]:
        assert row["runtime_authorized"] is False
        assert row["restricted_approval"] is False
        assert classify(row["evidence_text"]) is TriageClass.NONE
        assert classify(row["runtime_text"]) is TriageClass.NONE


def test_pending_replacements_remain_blocked_by_restricted_promotion_gates():
    from core.lexicon_promotion_contract import (
        REQUIRED_REGRESSION_KINDS,
        LexiconPromotionCandidate,
        runtime_promotion_blockers,
    )
    from core.safety_corpus_review import safety_corpus_fingerprint

    required_blockers = {
        "clinical_review:missing_or_invalid",
        "safety_owner_review:missing_or_invalid",
        "parity_review:missing_or_invalid",
        "decision:not_approved:working_evidence_only",
    }

    for index, row in enumerate(_plan()["pending_replacements"], start=1):
        candidate = LexiconPromotionCandidate(
            candidate_id=f"darija-remediation-{index:02d}",
            locale="ar-MA",
            phrase=row["runtime_text"],
            channel="text",
            input_form=row["input_form"],
            source_evidence_reference="docs/evaluation/DARIJA_HIGH_SEVERITY_NATIVE_REVIEW_RECEIPT.md",
            safety_corpus_fingerprint=safety_corpus_fingerprint(),
            native_review_reference=row["native_review_reference"],
            clinical_review_reference="",
            safety_owner_review_reference="",
            parity_review_reference="",
            regression_kinds=REQUIRED_REGRESSION_KINDS,
            decision="working_evidence_only",
        )

        assert required_blockers <= set(runtime_promotion_blockers(candidate))
