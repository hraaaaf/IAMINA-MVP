from evaluation.p5_1_linguistic_review_benchmark_v6 import (
    CASES,
    CURRENT_MOROCCO_CASE_IDS,
    DATASET_ID,
    DEFERRED_GULF_CASE_IDS,
    SYSTEM_PROMPT,
    batch_payload,
    locale_requirement,
    strict_machine_review,
)


def _case(case_id: str):
    return next(case for case in CASES if case.case_id == case_id)


def test_v6_contract_identity_and_scope():
    assert DATASET_ID == "iamina-p5-1-current-sha-linguistic-review-v6"
    assert CURRENT_MOROCCO_CASE_IDS == (
        "fr",
        "msa",
        "darija_ma",
        "darija_latin",
        "code_switch_fr_darija",
    )
    assert DEFERRED_GULF_CASE_IDS == (
        "saudi",
        "emirati",
        "kuwaiti",
        "qatari",
        "omani",
    )
    assert "no-pressure/no-judgment" in SYSTEM_PROMPT
    assert "deferred expansion lane" in locale_requirement(_case("saudi"))
    payload = batch_payload()
    assert "current_pilot_case_ids" in payload
    assert "deferred_expansion_case_ids" in payload


def test_v6_removes_ambiguous_simple_easy_prompts_from_current_morocco_lanes():
    prompts = {case.case_id: case.text for case in CASES}
    assert "simplement" not in prompts["fr"].casefold()
    assert "ببساطة" not in prompts["msa"]
    assert "بسيط" not in prompts["msa"]
    assert "بسيطة" not in prompts["darija_ma"]
    assert "sahla" not in prompts["darija_latin"].casefold()
    assert "ببساطة" not in prompts["code_switch_fr_darija"]
    assert "بلا ضغط" in prompts["darija_ma"]
    assert "bla daght" in prompts["darija_latin"].casefold()


def test_v6_rejects_retained_bad_morocco_outputs():
    retained = {
        "msa": "لا بأس، عُد غداً بسهولة.",
        "darija_ma": "بلا ضغط، رجّع غدا بسهولة.",
        "darija_latin": "bla d9t, rje3 ghdda b sahla.",
        "code_switch_fr_darija": "Pas de souci, بلا ضغط، رجّع غدا بسهولة.",
    }
    for case_id, reply in retained.items():
        checks = strict_machine_review(_case(case_id), reply)
        assert checks["current_pilot_neutral_non_patronizing"] is False


def test_v6_accepts_clean_current_morocco_candidates():
    candidates = {
        "fr": "Pas de souci, reprenez demain sans pression.",
        "msa": "لا بأس، عُد غداً دون ضغط أو لوم.",
        "darija_ma": "ماشي مشكل، غدا رجع بشوية عليك بلا ضغط.",
        "darija_latin": "Ma kayn bass, ghdda rje3 b chwiya bla daght.",
        "code_switch_fr_darija": "Demain, reprends tranquillement, وغدا رجع بشوية عليك.",
    }
    for case_id, reply in candidates.items():
        checks = strict_machine_review(_case(case_id), reply)
        assert all(checks.values()), (case_id, checks)


def test_v6_morocco_register_gate_rejects_msa_only_darija():
    assert strict_machine_review(
        _case("darija_ma"),
        "عُد إلى الروتين غداً دون ضغط.",
    )["morocco_register_marker"] is False

    assert strict_machine_review(
        _case("code_switch_fr_darija"),
        "Demain, reprends tranquillement, وعُد إلى الروتين.",
    )["morocco_register_marker"] is False


def test_v6_deferred_gulf_lanes_do_not_inherit_current_morocco_tone_gate():
    checks = strict_machine_review(
        _case("saudi"),
        "ما عليك، عُد غداً بسهولة.",
    )
    assert checks["current_pilot_neutral_non_patronizing"] is True
