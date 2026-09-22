from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.companion.clinical import get_advice_resolution
from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.domain_context import DomainContext


def _resolution() -> AdviceResolution:
    return AdviceResolution(
        decision=AdviceDecision(
            intent="test",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="test.rule",
            rule_version="1",
            allowed_actions=("explain",),
        ),
        reply="ok",
    )


def test_get_advice_resolution_applies_module_validation_once():
    resolution = _resolution()
    engine = SimpleNamespace(
        resolve_patient_advice=lambda *args, **kwargs: resolution,
        validate_advice_resolution=lambda value: value,
    )
    with patch("core.companion.clinical._resolve_engine", return_value=engine):
        result = get_advice_resolution(
            42,
            "message",
            DomainContext.empty(language="fr"),
            language="fr",
        )

    assert result is resolution


def test_validation_rejection_propagates_fail_closed():
    resolution = _resolution()

    def reject(_value):
        raise PermissionError("validation gate rejected")

    engine = SimpleNamespace(
        resolve_patient_advice=lambda *args, **kwargs: resolution,
        validate_advice_resolution=reject,
    )
    with patch("core.companion.clinical._resolve_engine", return_value=engine):
        with pytest.raises(PermissionError, match="validation gate rejected"):
            get_advice_resolution(
                42,
                "message",
                DomainContext.empty(language="fr"),
                language="fr",
            )
