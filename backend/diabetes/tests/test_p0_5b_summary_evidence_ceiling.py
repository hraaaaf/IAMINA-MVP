from companion.parser import parse_llm_json
from companion.prompts import SUMMARY_USER
from core.epistemic_safety import violates_epistemic_claim_policy


_DOCTOR_FIELDS = ["narrative", "key_insight", "doctor_brief"]


def test_summary_prompt_is_kpi_only_even_if_legacy_patterns_argument_is_passed():
    rendered = SUMMARY_USER.format(
        window_days=14,
        stats="TIR: 72%\nCV: 31%",
        patterns="- [1] SOMOGYI_REBOUND: overnight low then morning rise",
    )

    assert "TIR: 72%" in rendered
    assert "CV: 31%" in rendered
    assert "SOMOGYI_REBOUND" not in rendered
    assert "overnight low then morning rise" not in rendered
    assert "Patterns détectés" not in rendered
    assert "collation" not in rendered.lower()
    assert "association ou une séquence temporelle" in rendered
    assert "Ne nomme aucun syndrome" in rendered


def test_safe_doctor_brief_fields_survive_parser_boundary():
    payload = (
        '{"narrative":"Les mesures enregistrées sont résumées sur la période.",'
        '"key_insight":"Le TIR enregistré est de 72% sur la période.",'
        '"doctor_brief":"TIR 72%; CV 31%; 14 jours de données."}'
    )

    parsed = parse_llm_json(payload, _DOCTOR_FIELDS)

    assert parsed["narrative"]
    assert parsed["key_insight"] == "Le TIR enregistré est de 72% sur la période."
    assert parsed["doctor_brief"].startswith("TIR 72%")


def test_french_causal_or_named_mechanism_claim_fails_field_closed():
    payload = (
        '{"narrative":"Cette tendance confirme le phénomène de l aube.",'
        '"key_insight":"Le TIR enregistré est de 72%.",'
        '"doctor_brief":"TIR 72%; 14 jours de données."}'
    )

    parsed = parse_llm_json(payload, _DOCTOR_FIELDS)

    assert parsed["narrative"] == ""
    assert parsed["key_insight"] == "Le TIR enregistré est de 72%."
    assert parsed["doctor_brief"] == "TIR 72%; 14 jours de données."


def test_english_intervention_claim_fails_field_closed():
    payload = (
        '{"narrative":"The recorded values are summarized for this period.",'
        '"key_insight":"A bedtime snack could help this pattern.",'
        '"doctor_brief":"TIR 72%; CV 31%."}'
    )

    parsed = parse_llm_json(payload, _DOCTOR_FIELDS)

    assert parsed["narrative"]
    assert parsed["key_insight"] == ""
    assert parsed["doctor_brief"] == "TIR 72%; CV 31%."


def test_arabic_assertive_causality_fails_field_closed():
    payload = (
        '{"narrative":"هذه البيانات تؤكد السبب والآلية.",'
        '"key_insight":"تم تلخيص القياسات المسجلة.",'
        '"doctor_brief":"72%"}'
    )

    parsed = parse_llm_json(payload, _DOCTOR_FIELDS)

    assert parsed["narrative"] == ""
    assert parsed["key_insight"] == "تم تلخيص القياسات المسجلة."


def test_safe_uncertainty_language_does_not_trigger_overclaim_guard():
    assert not violates_epistemic_claim_policy(
        "This observation alone is not enough to establish a cause or diagnosis."
    )
    assert not violates_epistemic_claim_policy(
        "Cette observation ne suffit pas à établir une cause ou un diagnostic."
    )


def test_non_doctor_parser_schema_is_not_reclassified_by_p0_5b():
    payload = '{"reply":"This data confirms the diagnosis of diabetes."}'

    parsed = parse_llm_json(payload, ["reply"])

    assert parsed["reply"] == "This data confirms the diagnosis of diabetes."
