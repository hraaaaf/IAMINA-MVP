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
        fallback_content="C'est certainement une cause clinique.",
        fallback_action="Prends 10 unités avant le repas.",
    )


def test_fallback_summary_discards_legacy_clinical_authority():
    insights = _format_fallback([_pattern()], "fr")
    insight = insights[0]

    assert insight["code"] == "SYNTHETIC"
    assert insight["priority"] == 1
    assert insight["icon"] == "shield"
    assert insight["title"] == "Observation dans tes données"
    assert "cause ou un diagnostic" in insight["content"]
    assert "10 unités" not in insight["action"]
    assert "certainement" not in insight["content"]


def test_llm_formatted_summary_discards_adversarial_claims():
    payload = json.dumps(
        [
            {
                "code": "SYNTHETIC",
                "title": "Effet Somogyi confirmé",
                "content": "Cette séquence prouve la cause hormonale.",
                "action": "Increase your insulin dose tonight.",
            }
        ]
    )
    insights = _parse_insights_json(payload, [_pattern()], "en")
    insight = insights[0]

    assert insight["code"] == "SYNTHETIC"
    assert insight["title"] == "Observation in your data"
    assert "not enough to establish a cause or diagnosis" in insight["content"]
    assert "Somogyi" not in insight["title"]
    assert "hormonal" not in insight["content"]
    assert "insulin" not in insight["action"].lower()
