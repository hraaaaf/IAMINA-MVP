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


def test_latest_human_review_cutover_is_reflected_in_runtime_inventory():
    runtime = _runtime_inventory()
    removed = {
        ("latin_transliteration", "ghadi ntah"),
        ("latin_transliteration", "fqad l3ql"),
        ("latin_transliteration", "fqdt l3ql"),
        ("latin_transliteration", "fqedt l3a9l"),
        ("latin_transliteration", "f9edt l3a9l"),
        ("latin_transliteration", "f9dt l3ql"),
        ("latin_transliteration", "tahwid"),
        ("latin_transliteration", "kanr3ed"),
        ("latin_transliteration", "kanr3ad"),
        ("latin_transliteration", "rj fou"),
        ("latin_transliteration", "rajef"),
        ("latin_transliteration", "ma kan7ml"),
        ("latin_transliteration", "dwakht"),
        ("latin_transliteration", "dayakht"),
        ("latin_transliteration", "dwekh"),
        ("latin_transliteration", "dawkhani"),
    }
    promoted = {
        ("latin_transliteration", "dekht"),
        ("latin_transliteration", "fiya doukha"),
        ("latin_transliteration", "kantra33ad"),
    }
    reapproved = {
        ("latin_transliteration", "kantih"),
        ("latin_transliteration", "kayrjraj"),
        ("latin_transliteration", "ma kanchoufch"),
        ("arabic_script", "غادي نغمى عليا"),
        ("arabic_script", "غادي يغمى عليا"),
    }

    assert removed.isdisjoint(runtime)
    assert promoted <= runtime
    assert reapproved <= runtime


def test_latest_human_review_cutover_classifier_behavior():
    from core.triage_classification import TriageClass, classify

    removed_texts = (
        "ghadi ntah",
        "fqad l3ql",
        "fqdt l3ql",
        "fqedt l3a9l",
        "f9edt l3a9l",
        "f9dt l3ql",
        "tahwid",
        "kanr3ed",
        "kanr3ad",
        "rj fou",
        "rajef",
        "ma kan7ml",
        "dwakht",
        "dayakht",
        "dwekh",
        "dawkhani",
    )
    for text in removed_texts:
        assert classify(text) is TriageClass.NONE

    for text in ("dekht", "fiya doukha", "kantra33ad"):
        assert classify(text) is TriageClass.GLYCEMIC_EMERGENCY

    assert classify("ma kan7mlch") is TriageClass.GLYCEMIC_EMERGENCY
    assert classify("غادي نغمى عليا") is TriageClass.GLYCEMIC_EMERGENCY
    assert classify("غادي يغمى عليا") is TriageClass.GLYCEMIC_EMERGENCY


def test_all_native_accepted_existing_variants_remain_in_runtime_after_cutover():
    # The historical native-review fixture is preserved as evidence. The latest
    # qualified-human review supersedes only explicitly challenged rows.
    accepted = {
        (row["input_form"], row["text"])
        for row in _outcomes()
        if row["native_evidence_status"] == "accepted_exact_native_evidence"
    }

    assert len(accepted) == 15
    assert accepted <= _runtime_inventory()


def test_historical_pending_replacements_remain_inactive():
    from core.triage_classification import TriageClass, classify

    # These candidates belong to the older staging packet. The 2026-09-12 human
    # review approved different replacements, so the historical candidates stay
    # blocked and must not become active accidentally.
    for row in _plan()["pending_replacements"]:
        assert row["runtime_authorized"] is False
        assert row["restricted_approval"] is False
        assert classify(row["evidence_text"]) is TriageClass.NONE
        assert classify(row["runtime_text"]) is TriageClass.NONE


def test_historical_pending_replacements_remain_blocked_by_promotion_gates():
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
