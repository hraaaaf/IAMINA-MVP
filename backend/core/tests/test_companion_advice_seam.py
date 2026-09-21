from unittest.mock import patch

import pytest

from core.companion import clinical
from core.contracts.domain_context import DomainContext
from diabetes.services.clinical.engine import DiabetesEngine


def test_diabetes_engine_exposes_food_decision_through_base_engine_seam():
    resolution = DiabetesEngine().resolve_advice(
        "je peux manger un mille feuille !?",
        DomainContext.empty(language="fr"),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.food.permission"
    assert resolution.decision.authority_level.value == "L2"


def test_core_advice_resolver_rejects_invalid_module_resolution_type():
    class BadEngine:
        def resolve_advice(
            self,
            message,
            context,
            language="fr",
            previous_user_message=None,
        ):
            return {"decision": "not-governed"}

    with patch("core.companion.clinical._resolve_engine", return_value=BadEngine()):
        with pytest.raises(TypeError, match="invalid AdviceResolution"):
            clinical.get_advice_resolution(
                42,
                "je peux manger un mille feuille !?",
                DomainContext.empty(language="fr"),
                language="fr",
            )
