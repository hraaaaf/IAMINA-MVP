from datetime import date

from evaluation import p5_1_linguistic_review_benchmark_v8 as v8
from evaluation.p5_1_linguistic_review_benchmark_v8 import (
    CASES,
    DATASET_ID,
    SYSTEM_PROMPT,
    batch_payload,
    locale_requirement,
    strict_machine_review,
)


def _case(case_id: str):
    return next(case for case in CASES if case.case_id == case_id)


def test_v8_contract_identity_and_human_feedback():
    assert DATASET_ID == "iamina-p5-1-current-sha-linguistic-review-v8"
    assert "Retained human Morocco review" in SYSTEM_PROMPT
    assert "ما تقلقش" in SYSTEM_PROMPT
    assert "t9der terja3" in SYSTEM_PROMPT
    assert "avoid ما تشدش" in locale_requirement(_case("darija_ma"))
    latin_requirement = locale_requirement(_case("darija_latin"))
    assert "avoid nrj3" in latin_requirement
    assert "second person" in latin_requirement
    payload = batch_payload().casefold()
    assert "second person" in payload


def test_v8_source_prompt_does_not_seed_flagged_nrj3():
    prompt = _case("darija_latin").text.casefold()
    assert "nrj3" not in prompt
    assert "katkhatebni ana direct" in prompt


def test_v8_rejects_exact_human_flagged_outputs():
    ar_checks = strict_machine_review(
        _case("darija_ma"),
        "ما تشدش، غدا تقدر ترجع بلا ضغط.",
    )
    assert ar_checks["retained_human_darija_feedback"] is False

    latin_checks = strict_machine_review(
        _case("darija_latin"),
        "Mashi mouchkil, ghdda nrj3 bla daght.",
    )
    assert latin_checks["retained_human_darija_feedback"] is False


def test_v8_accepts_human_corrected_darija_examples():
    ar_checks = strict_machine_review(
        _case("darija_ma"),
        "ما تقلقش، غدا تقدر ترجع بلا ضغط.",
    )
    assert all(ar_checks.values()), ar_checks

    latin_examples = (
        "Mashi mouchkil, ghdda t9der terja3 bla daght.",
        "Mashi mouchkil, ghdda t9der t3awed bla daght.",
    )
    for reply in latin_examples:
        checks = strict_machine_review(_case("darija_latin"), reply)
        assert all(checks.values()), (reply, checks)


def test_v8_preserves_other_clean_morocco_lanes():
    candidates = {
        "fr": "Pas de souci, reprenez demain sans pression.",
        "msa": "لا تقلق، يمكنك العودة غداً دون ضغط.",
        "code_switch_fr_darija": "Pas de problème, غدا تقدر ترجع بلا ضغط وبلا لوم.",
    }
    for case_id, reply in candidates.items():
        checks = strict_machine_review(_case(case_id), reply)
        assert all(checks.values()), (case_id, checks)


def test_v8_run_benchmark_binds_effective_base6_contract(monkeypatch, tmp_path):
    captured = {}

    def fake_run_benchmark(*, output_path, today):
        captured["dataset_id"] = v8.base7.base6.DATASET_ID
        captured["case_prompt"] = next(
            case.text for case in v8.base7.base6.CASES if case.case_id == "darija_latin"
        )
        captured["system_prompt"] = v8.base7.base6.SYSTEM_PROMPT
        captured["payload"] = v8.base7.base6.batch_payload()
        captured["checks"] = v8.base7.base6.strict_machine_review(
            _case("darija_latin"),
            "Mashi mouchkil, ghdda t9der terja3 bla daght.",
        )
        return {"source_sha": "test-sha"}

    monkeypatch.setattr(v8.base7.base6, "run_benchmark", fake_run_benchmark)
    report = v8.run_benchmark(
        output_path=tmp_path / "report.json",
        today=date(2026, 9, 12),
    )

    assert report["dataset_id"] == DATASET_ID
    assert captured["dataset_id"] == DATASET_ID
    assert "nrj3" not in captured["case_prompt"].casefold()
    assert "Retained human Morocco review" in captured["system_prompt"]
    assert "t9der/t9dar" in captured["payload"]
    assert captured["checks"]["retained_human_darija_feedback"] is True
