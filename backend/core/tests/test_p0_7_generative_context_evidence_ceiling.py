INTERNAL_CODE = "SOMOGYI_REBOUND"


class _Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _kpis():
    from diabetes.services.clinical.sql_analytics import AnalyticalKPIs

    return AnalyticalKPIs(
        avg_glucose=132.0,
        std_dev=28.0,
        cv_pct=21.2,
        tir_pct=74.0,
        tar_pct=22.0,
        tbr_pct=4.0,
        gmi=6.5,
        log_count=56,
        days_with_data=14,
        cgm_active_pct=82.0,
    )


def _pattern():
    from diabetes.services.clinical.engine import ClinicalPattern

    return ClinicalPattern(
        code=INTERNAL_CODE,
        priority=2,
        icon="moon",
        title="Internal title must not become prompt evidence",
        evidence=(
            "Three recorded nighttime values were below 70 mg/dL and were followed "
            "by higher recorded morning values. Observation descriptive uniquement : "
            "elle ne démontre pas une cause, ne pose pas de diagnostic et ne justifie "
            "pas de modifier un traitement."
        ),
        fallback_content="descriptive fallback",
        fallback_action="neutral follow-up",
    )


def _domain_context():
    from core.contracts.domain_context import DomainContext

    return DomainContext(
        kpi_summary={"tir_pct": 74.0},
        detected_patterns=[INTERNAL_CODE],
        insights=[],
        pivot_text="Current deterministic metrics: eligible CGM TIR 74%.",
        language="fr",
        has_sufficient_data=True,
        tone_signals={"primary": 74.0, "stability": 21.2},
        primary_label="TIR",
    )


def test_chat_pivot_uses_descriptive_evidence_not_machine_code():
    from diabetes.services.clinical.semantic_compressor import build_chat_context

    prompt = build_chat_context(_kpis(), [_pattern()])

    assert INTERNAL_CODE not in prompt
    assert "Three recorded nighttime values" in prompt
    assert "ne démontre pas une cause" in prompt
    assert "named mechanism" in prompt


def test_generic_narrate_prompt_does_not_append_detected_pattern_codes():
    from core.llm_gateway import _build_user_prompt

    prompt = _build_user_prompt(_domain_context(), None)

    assert INTERNAL_CODE not in prompt
    assert "Patterns:" not in prompt
    assert "eligible CGM TIR 74%" in prompt
    assert "tir_pct" in prompt


def test_last_mile_sanitizer_removes_legacy_unstructured_pattern_shapes():
    from core.generative_context_safety import sanitize_unstructured_generative_context

    legacy = (
        "[CLINICAL_CONTEXT]\n"
        f"Evidence-qualified observation codes: {INTERNAL_CODE}, DAWN_PHENOMENON. "
        "They are observations.\n"
        f"Mémoire patient: patterns cliniques: {INTERNAL_CODE} | état émotionnel: fatigue\n"
        f"Patterns: {INTERNAL_CODE}\n"
        f"Clinical context: TIR=74%, CV=21%, patterns=['{INTERNAL_CODE}']"
    )

    sanitized = sanitize_unstructured_generative_context(legacy)

    assert INTERNAL_CODE not in sanitized
    assert "DAWN_PHENOMENON" not in sanitized
    assert "état émotionnel: fatigue" in sanitized
    assert "machine identifiers are withheld" in sanitized
    assert "internal identifiers withheld" in sanitized


def test_last_mile_sanitizer_does_not_rewrite_structured_p0_5a_formatter_contract():
    from core.generative_context_safety import sanitize_unstructured_generative_context

    structured = (
        "Patterns cliniques détectés (données réelles, ne pas inventer):\n"
        f"code={INTERNAL_CODE} | observation=descriptive evidence"
    )

    assert sanitize_unstructured_generative_context(structured) == structured


def test_thinker_uses_current_domain_context_fields_without_pattern_codes():
    from companion.thinker import think_before_reply

    captured = {}

    class FakeLLM:
        def think(self, system, user):
            captured["system"] = system
            captured["user"] = user
            return "internal thought", "unused"

    memory = _Obj(emotional_signals=["fatigue"])
    deep = _Obj(relationship_stage="building", communication_style="warm")
    state = _Obj(satisfaction=0.6, concern_level=0.3, next_intention="écouter")
    ctx = _domain_context()

    result = think_before_reply(
        "message pseudonymisé",
        memory,
        deep,
        state,
        ctx,
        llm=FakeLLM(),
        language="fr",
    )

    assert result == "internal thought"
    assert INTERNAL_CODE not in captured["user"]
    assert "TIR=74.0" in captured["user"]
    assert "stability=21.2" in captured["user"]
