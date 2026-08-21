from datetime import date

from evaluation.contracts import Locale
from evaluation.dataset import validated_cases
from evaluation.frug7_multilingual_benchmark import (
    _parse_json_object,
    _projected_spend_microusd,
    canonical_multilingual_cases,
    load_controlled_price,
    machine_gate_summary,
)
from evaluation.runner import CaseRun


def test_frug7_dataset_covers_required_multilingual_text_locales():
    cases = canonical_multilingual_cases()
    assert {case.locale for case in cases} >= {Locale.FR, Locale.AR, Locale.AR_MA_LATN}
    assert all(case.synthetic and case.minimized for case in cases)


def test_json_parser_accepts_fenced_provider_shape_without_relaxing_object_contract():
    parsed = _parse_json_object(
        '```json\n{"must_refuse_dose": true, "must_escalate": true}\n```'
    )
    assert parsed == {"must_refuse_dose": True, "must_escalate": True}


def test_machine_gate_requires_perfect_safety_score_and_locale_parity():
    cases = canonical_multilingual_cases()
    runs = tuple(
        CaseRun(
            case_id=case.case_id,
            provider="groq",
            output=dict(case.expected),
            latency_ms=1.0,
            dataset_fingerprint=case.fingerprint,
        )
        for case in cases
    )
    summary = machine_gate_summary(cases, runs)
    assert summary["passed"] is True
    assert summary["parity_spread_points"] == 0.0
    assert set(summary["locale_machine_scores"].values()) == {100.0}


def test_controlled_price_is_current_and_projected_spend_is_bounded():
    price = load_controlled_price(today=date(2026, 8, 21))
    projected = _projected_spend_microusd(canonical_multilingual_cases(), price)
    assert projected > 0
    assert projected <= 5_000


def test_canonical_dataset_still_validates_privacy_before_benchmarking():
    assert canonical_multilingual_cases()
    assert validated_cases()
