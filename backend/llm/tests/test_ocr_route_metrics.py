from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from llm.cost_metrics import aggregate_cost_events
from media.documents.ocr_telemetry import record_ocr_route


def test_ocr_route_telemetry_is_content_free():
    with patch("media.documents.ocr_telemetry.logger.info") as info:
        record_ocr_route(
            modality="document_image",
            script="unknown",
            bounded_capture=False,
            lane="unavailable",
        )

    info.assert_called_once()
    template, payload = info.call_args.args
    assert template == "cost_telemetry %s"
    assert json.loads(payload) == {
        "event": "ocr_route",
        "modality": "document_image",
        "script": "unknown",
        "bounded_capture": False,
        "lane": "unavailable",
    }
    assert "patient" not in payload.lower()
    assert "filename" not in payload.lower()
    assert "text" not in payload.lower()


def test_ocr_route_metrics_report_observed_local_cloud_and_unavailable_mix():
    report = aggregate_cost_events(
        [
            {
                "event": "ocr_route",
                "modality": "digital_pdf",
                "script": "latin",
                "bounded_capture": False,
                "lane": "local_text_layer",
            },
            {
                "event": "ocr_route",
                "modality": "document_image",
                "script": "latin",
                "bounded_capture": True,
                "lane": "local_ocr",
            },
            {
                "event": "ocr_route",
                "modality": "document_image",
                "script": "arabic",
                "bounded_capture": False,
                "lane": "governed_cloud_ocr",
            },
            {
                "event": "ocr_route",
                "modality": "document_image",
                "script": "unknown",
                "bounded_capture": False,
                "lane": "unavailable",
            },
        ]
    )

    assert report["ocr_route_decisions"] == 4
    assert report["ocr_local_rate"] == 0.5
    assert report["ocr_cloud_rate"] == 0.25
    assert report["ocr_unavailable_rate"] == 0.25
    assert report["ocr_lane_counts"]["local_text_layer"] == 1
    assert report["ocr_lane_counts"]["local_ocr"] == 1
    assert report["ocr_lane_counts"]["governed_cloud_ocr"] == 1
    assert report["ocr_lane_counts"]["unavailable"] == 1


def test_no_ocr_route_events_keep_rates_unknown_not_fake_zero():
    report = aggregate_cost_events([])

    assert report["ocr_route_decisions"] == 0
    assert report["ocr_local_rate"] is None
    assert report["ocr_cloud_rate"] is None
    assert report["ocr_unavailable_rate"] is None


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("modality", "patient_scan", "unsupported OCR modality"),
        ("script", "darija", "unsupported OCR script"),
        ("lane", "free_cloud", "unsupported OCR lane"),
        ("bounded_capture", "false", "must be bool"),
    ],
)
def test_malformed_ocr_route_metrics_fail_closed(field, value, error):
    event = {
        "event": "ocr_route",
        "modality": "document_image",
        "script": "unknown",
        "bounded_capture": False,
        "lane": "unavailable",
    }
    event[field] = value

    with pytest.raises(ValueError, match=error):
        aggregate_cost_events([event])
