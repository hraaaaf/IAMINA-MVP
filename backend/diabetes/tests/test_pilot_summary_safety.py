import json

from diabetes.services.clinical.engine import (
    ClinicalPattern,
    _format_fallback,
    _parse_insights_json,
)


def _pattern() -> ClinicalPattern:
    return ClinicalPattern(
        code="SYNTHETIC",
        priority=1,
        icon="shield",
        title="Synthetic pattern",
        evidence="Synthetic evidence",
        fallback_content="Observation only.",
        fallback_action="Prends 10 unités avant le repas.",
    )


def test_fallback_summary_action_is_sanitized():
    insights = _format_fallback([_pattern()], "fr")
    assert "Je ne peux pas prescrire" in insights[0]["action"]


def test_llm_formatted_summary_action_is_sanitized():
    payload = json.dumps(
        [
            {
                "code": "SYNTHETIC",
                "title": "Synthetic",
                "content": "Observation only.",
                "action": "Increase your insulin dose tonight.",
            }
        ]
    )
    insights = _parse_insights_json(payload, [_pattern()], "en")
    assert "I cannot prescribe treatment" in insights[0]["action"]
