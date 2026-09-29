import json
import logging

import pytest

from companion.protected_shadow_telemetry import record_protected_narration_shadow
from llm.cost_event_store import validate_cost_event


def _events(caplog):
    prefix = "cost_telemetry "
    return [
        json.loads(record.message[len(prefix):])
        for record in caplog.records
        if record.name == "iamina.cost" and record.message.startswith(prefix)
    ]


def test_protected_shadow_telemetry_is_content_free(caplog, monkeypatch):
    persisted = []
    monkeypatch.setattr(
        "companion.protected_shadow_telemetry.persist_cost_event",
        lambda event: persisted.append(event),
    )

    with caplog.at_level(logging.INFO, logger="iamina.cost"):
        record_protected_narration_shadow(status="accepted")
        record_protected_narration_shadow(status="rejected")

    expected = [
        {
            "event": "protected_narration_shadow",
            "status": "accepted",
            "provider": "groq",
            "family": "clinician_prep",
        },
        {
            "event": "protected_narration_shadow",
            "status": "rejected",
            "provider": "groq",
            "family": "clinician_prep",
        },
    ]
    assert _events(caplog) == expected
    assert persisted == expected
    assert "patient" not in caplog.text.lower()
    assert "prompt" not in caplog.text.lower()
    assert "reply" not in caplog.text.lower()


def test_protected_shadow_event_passes_finops_allowlist():
    event = {
        "event": "protected_narration_shadow",
        "status": "blocked",
        "provider": "groq",
        "family": "clinician_prep",
    }
    assert validate_cost_event(event) == event


@pytest.mark.parametrize("field,value", [
    ("status", "patient-42"),
    ("provider", "other"),
    ("family", "food"),
])
def test_protected_shadow_telemetry_rejects_unbounded_labels(field, value):
    kwargs = {
        "status": "accepted",
        "provider": "groq",
        "family": "clinician_prep",
    }
    kwargs[field] = value
    with pytest.raises(ValueError):
        record_protected_narration_shadow(**kwargs)
