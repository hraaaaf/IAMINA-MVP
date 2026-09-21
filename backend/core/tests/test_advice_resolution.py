import pytest

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution


def _decision():
    return AdviceDecision(
        intent="education",
        authority_level=AdviceAuthorityLevel.L1_EDUCATION,
        decision=AdviceDisposition.CONSTRAIN,
        rule_id="test.rule",
        rule_version="1",
        allowed_actions=("explain",),
    )


def test_advice_resolution_is_immutable_and_requires_reply():
    resolution = AdviceResolution(decision=_decision(), reply="  Safe reply.  ")
    assert resolution.reply == "Safe reply."

    with pytest.raises(ValueError, match="reply is required"):
        AdviceResolution(decision=_decision(), reply="   ")


def test_advice_resolution_requires_governed_decision():
    with pytest.raises(ValueError, match="decision must be"):
        AdviceResolution(decision=object(), reply="Safe reply.")  # type: ignore[arg-type]
