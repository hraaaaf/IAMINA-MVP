import pytest

from evaluation.frug5_call_rate_delta import (
    BASELINE_ROUTER_BLOB,
    BASELINE_ROUTER_COMMIT,
    CASES,
    baseline_route,
    build_call_rate_report,
    current_route,
)


def test_call_rate_delta_is_material_on_same_controlled_corpus():
    report = build_call_rate_report()

    assert report["evidence_scope"] == "controlled_synthetic_route_mix_not_production"
    assert report["interactions"] == 12
    assert report["baseline"] == {
        "llm_calls": 8,
        "zero_model_calls": 4,
        "llm_call_rate_per_interaction": pytest.approx(2 / 3),
    }
    assert report["current"] == {
        "llm_calls": 4,
        "zero_model_calls": 8,
        "llm_call_rate_per_interaction": pytest.approx(1 / 3),
    }
    assert report["absolute_rate_delta"] == pytest.approx(-1 / 3)
    assert report["relative_llm_call_reduction"] == pytest.approx(0.5)


def test_baseline_is_traceable_to_pre_farewell_router():
    assert BASELINE_ROUTER_COMMIT == "299676ca99c357f6146eb772048eeeaa6a10c2af"
    assert BASELINE_ROUTER_BLOB == "80ec292ebe2032503d45117555cb84e89d1a0320"
    assert baseline_route("au revoir") == "llm"
    assert baseline_route("goodbye") == "llm"
    assert baseline_route("مع السلامة") == "llm"
    assert baseline_route("bslama") == "llm"


def test_existing_zero_model_routes_do_not_regress():
    stable = [case for case in CASES if case.baseline_route == "zero_model"]
    assert stable
    for case in stable:
        assert baseline_route(case.message) == "zero_model"
        assert current_route(case.message, case.locale) == "zero_model"


def test_new_farewell_bypass_is_locale_bounded_and_exact():
    farewells = [case for case in CASES if "farewell" in case.case_id]
    assert {case.locale for case in farewells} >= {"fr", "en", "ar", "ar-MA"}
    assert current_route("au revoir", "fr") == "zero_model"
    assert current_route("goodbye", "en") == "zero_model"
    assert current_route("مع السلامة", "ar") == "zero_model"
    assert current_route("bslama", "ar-MA") == "zero_model"

    assert current_route("au revoir glycémie", "fr") == "llm"
    assert current_route("ok", "fr") == "llm"
    assert current_route("yes", "en") == "llm"
    assert current_route("no", "en") == "llm"


def test_open_health_questions_still_fall_through_to_governed_path():
    assert current_route("Pourquoi ma glycémie varie après le repas ?", "fr") == "llm"
    assert current_route("ليش السكر يتغير بعد الأكل؟", "ar") == "llm"
