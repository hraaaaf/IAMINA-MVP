import json
import logging

import pytest

from companion.route_telemetry import record_companion_route


def _route_events(caplog):
    prefix = "cost_telemetry "
    return [
        json.loads(record.message[len(prefix) :])
        for record in caplog.records
        if record.name == "iamina.cost" and record.message.startswith(prefix)
    ]


def test_companion_route_telemetry_is_content_free(caplog):
    with caplog.at_level(logging.INFO, logger="iamina.cost"):
        record_companion_route("safety")
        record_companion_route("zero_model")
        record_companion_route("llm")

    assert _route_events(caplog) == [
        {"event": "companion_route", "route": "safety"},
        {"event": "companion_route", "route": "zero_model"},
        {"event": "companion_route", "route": "llm"},
    ]
    assert "patient" not in caplog.text.lower()
    assert "prompt" not in caplog.text.lower()


def test_companion_route_telemetry_rejects_unbounded_labels():
    with pytest.raises(ValueError, match="unsupported companion route"):
        record_companion_route("patient-42")
