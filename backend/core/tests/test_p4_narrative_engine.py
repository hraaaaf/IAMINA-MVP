"""
Tests for P4 — LLM Narrative Engine Generalization.

Covers:
  T1: build_system_prompt() uses identity.companion_name
  T2: build_system_prompt() uses identity.domain_description
  T3: build_system_prompt() uses get_language_label() for language mapping
  T4: build_system_prompt() raises ValueError when sentinel drifts
  T5: narrate() delegates _build_system_prompt() to build_system_prompt()
  T6: structured insight formatting keeps its JSON contract behind the capability-aware gateway
  T7: IAmina.__init__ no longer stores self.llm
  T8: react() self-provisions the sanctioned gateway when none passed
  T9: summarize() self-provisions the sanctioned gateway when none passed
"""
from unittest.mock import MagicMock, patch

import pytest

from core.contracts.companion_identity import CompanionIdentity


@pytest.fixture
def diabetes_identity():
    return CompanionIdentity(
        companion_name="IAmina",
        domain_description="compagnon pour patient diabétique",
        unit="mg/dL",
    )


@pytest.fixture
def cardio_identity():
    return CompanionIdentity(
        companion_name="IAmina Cardio",
        domain_description="compagnon hypertension",
        unit="mmHg",
    )


def test_build_system_prompt_uses_companion_name(diabetes_identity):
    from companion.prompts import build_system_prompt

    result = build_system_prompt(diabetes_identity, "fr", "encouraging")
    assert "IAmina" in result


def test_build_system_prompt_uses_custom_companion_name(cardio_identity):
    from companion.prompts import build_system_prompt

    result = build_system_prompt(cardio_identity, "fr", "encouraging")
    assert "IAmina Cardio" in result
    assert "hypertension" in result


def test_build_system_prompt_uses_domain_description(cardio_identity):
    from companion.prompts import build_system_prompt

    result = build_system_prompt(cardio_identity, "fr", "gentle")
    assert "compagnon hypertension" in result
    assert "compagnon bienveillant pour patient diabétique" not in result


def test_build_system_prompt_uses_language_label(diabetes_identity):
    from companion.prompts import build_system_prompt, get_language_label

    result = build_system_prompt(diabetes_identity, "ar-MA", "encouraging")
    expected_label = get_language_label("ar-MA")
    assert expected_label in result


def test_build_system_prompt_french_label(diabetes_identity):
    from companion.prompts import build_system_prompt, get_language_label

    result = build_system_prompt(diabetes_identity, "fr", "encouraging")
    assert get_language_label("fr") in result


def test_build_system_prompt_raises_if_sentinel_not_found(diabetes_identity):
    from companion.prompts import build_system_prompt

    with patch("companion.prompts.SYSTEM_BASE", "Some prompt without the persona line."):
        with pytest.raises(ValueError, match="persona sentinel not found"):
            build_system_prompt(diabetes_identity, "fr")


@pytest.mark.django_db
def test_narrate_delegates_to_build_system_prompt():
    """This unit test isolates prompt delegation; egress policy is tested separately."""
    from core.contracts.domain_context import DomainContext
    from core.contracts.patient_context import ModulePatientContext
    from llm.base import LLMResponse

    patient_ctx = ModulePatientContext(
        patient_id=1,
        language="fr",
        region="MA",
        consent_flags={"ai_analysis": True},
    )
    domain_ctx = DomainContext(
        kpi_summary={"tir_pct": 72.0},
        detected_patterns=[],
        insights=[],
        pivot_text="Glucose stable.",
        language="fr",
    )
    identity = CompanionIdentity("IAmina Test", "test companion", "mg/dL")

    fake_response = LLMResponse(content="ok", provider="mock")
    mock_provider = MagicMock()
    mock_provider.complete.return_value = fake_response
    mock_provider.model_name = "mock"

    calls = []
    original = __import__(
        "companion.prompts",
        fromlist=["build_system_prompt"],
    ).build_system_prompt

    def tracking_build(id_, lang, tone="encouraging"):
        calls.append((id_.companion_name, lang, tone))
        return original(id_, lang, tone)

    with (
        patch("core.llm_gateway.assert_ai_egress_allowed"),
        patch("core.llm_gateway.get_llm", return_value=mock_provider),
        patch(
            "companion.prompts.build_system_prompt",
            side_effect=tracking_build,
        ),
    ):
        from core.llm_gateway import narrate

        narrate(patient_ctx, domain_ctx, identity, "fr")

    assert len(calls) == 1
    assert calls[0][0] == "IAmina Test"
    assert calls[0][1] == "fr"


def test_engine_format_with_llm_uses_capability_aware_gateway():
    import inspect

    from diabetes.services.clinical import engine

    source = inspect.getsource(engine._format_with_llm)
    assert "get_gateway_llm" in source
    assert "Capability.SURFACE_DETERMINISTIC_PATTERN" in source
    assert "narrate(" not in source, (
        "structured insight formatting keeps its endpoint-specific JSON contract"
    )


@pytest.mark.django_db
def test_iamina_init_has_no_llm_attribute():
    from companion.core import IAmina

    mock_patient = MagicMock()
    mock_patient.id = 1

    with (
        patch("companion.core.IAminaMemory") as mock_mem,
        patch("companion.core.IAminaDeepMemory") as mock_deep,
    ):
        mock_mem.load.return_value = MagicMock()
        mock_deep.load.return_value = MagicMock()
        iamina = IAmina(mock_patient, language="fr")

    assert not hasattr(iamina, "llm"), (
        "IAmina.__init__ must not store self.llm — LLM is provisioned lazily by sub-modules"
    )


def test_react_self_provisions_llm_when_none():
    from companion.reactor import react
    from llm.base import LLMResponse

    fake_response = LLMResponse(
        content='{"message": "Bien noté!", "tone_detected": "encouraging"}',
        provider="mock",
    )
    mock_llm = MagicMock()
    mock_llm.complete.return_value = fake_response

    mock_entry = MagicMock()
    mock_entry.blood_sugar = 120.0
    mock_entry.meal_type = "lunch"
    mock_entry.notes = ""

    mock_memory = MagicMock()
    mock_memory.current_tone = "encouraging"

    with patch(
        "companion.reactor.get_gateway_llm",
        return_value=mock_llm,
    ) as mock_get_gateway:
        react(mock_entry, mock_memory)
        mock_get_gateway.assert_called_once_with()


def test_summarize_self_provisions_llm_when_none():
    from companion.narrator import summarize

    mock_llm = MagicMock()
    mock_patient = MagicMock()
    mock_patient.id = 1
    mock_memory = MagicMock()
    mock_memory.current_tone = "encouraging"

    empty_ctx = MagicMock(has_sufficient_data=False)
    with (
        patch(
            "companion.narrator.get_gateway_llm",
            return_value=mock_llm,
        ) as mock_get_gateway,
        patch("companion.narrator.get_domain_context", return_value=empty_ctx),
    ):
        summarize(mock_patient, mock_memory)
        mock_get_gateway.assert_called_once_with()
