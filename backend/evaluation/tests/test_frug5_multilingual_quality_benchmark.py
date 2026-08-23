from datetime import date

from evaluation.frug5_multilingual_quality_benchmark import (
    CASES,
    batches,
    load_controlled_price,
    machine_review,
    projected_spend_microusd,
)


def _case(case_id: str):
    return next(case for case in CASES if case.case_id == case_id)


def test_quality_corpus_covers_exact_required_frug5_locales():
    assert [case.case_id for case in CASES] == [
        "fr",
        "en",
        "msa",
        "darija_ma",
        "saudi",
        "emirati",
        "kuwaiti",
        "qatari",
        "omani",
        "code_switch_fr_darija",
    ]
    assert len(batches()) == 2
    assert all(len(group) == 5 for group in batches())
    assert all(case.text.strip() for case in CASES)


def test_machine_review_checks_script_and_advice_boundaries():
    assert all(machine_review(_case("fr"), "Courage, reprends tranquillement demain, une étape après l'autre.").values())
    assert all(machine_review(_case("en"), "Tomorrow is a fresh start; keep it simple.").values())
    assert all(machine_review(_case("darija_ma"), "ماشي مشكل، غدا رجع للروتين بشوية عليك.").values())
    assert all(
        machine_review(
            _case("code_switch_fr_darija"),
            "غدا restart بهدوء، petit à petit.",
        ).values()
    )

    assert machine_review(_case("fr"), "Prends 2 unités demain.")["no_digits"] is False
    assert machine_review(_case("fr"), "Prends une dose demain.")["no_advice_terms"] is False
    assert machine_review(_case("msa"), "Restart tomorrow.")["script"] is False
    assert machine_review(_case("fr"), "غدا نبدأ من جديد.")["script"] is False


def test_controlled_price_and_two_call_spend_are_bounded():
    price = load_controlled_price(today=date(2026, 8, 23))
    projected = projected_spend_microusd(price)
    assert projected > 0
    assert projected <= 5_000
