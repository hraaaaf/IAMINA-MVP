import json

import pytest

from llm.finops_audit import (
    aggregate_usage_dimensions,
    build_finops_audit_report,
    detect_usage_anomalies,
    emit_finops_audit_alerts,
    emit_usage_anomaly_alerts,
)


def _events():
    rogue = {
        "patient_id": 4242,
        "prompt": "PRIVATE-PROMPT",
        "object_key": "patient/4242/report.pdf",
    }
    return [
        {
            "event": "llm_usage",
            "status": "success",
            "input_tokens": 120,
            "output_tokens": 30,
            "cached_input_tokens": 20,
            "total_tokens": 150,
            **rogue,
        },
        {
            "event": "metered_usage",
            "status": "success",
            "modality": "ocr",
            "unit": "pages",
            "quantity": 8,
            **rogue,
        },
        {
            "event": "metered_usage",
            "status": "success",
            "modality": "vision",
            "unit": "images",
            "quantity": 6,
            **rogue,
        },
        {
            "event": "metered_usage",
            "status": "success",
            "modality": "stt",
            "unit": "seconds",
            "quantity": 120,
            **rogue,
        },
        {
            "event": "metered_usage",
            "status": "success",
            "modality": "tts",
            "unit": "characters",
            "quantity": 400,
            **rogue,
        },
        {
            "event": "media_bytes",
            "action": "uploaded",
            "bytes": 4_000_000,
            **rogue,
        },
    ]


def test_usage_dimensions_cover_tokens_pages_images_audio_and_bytes_without_payload():
    dimensions = aggregate_usage_dimensions(_events())

    assert dimensions == {
        "llm:cached_input_tokens": 20,
        "llm:input_tokens": 120,
        "llm:output_tokens": 30,
        "llm:total_tokens": 150,
        "media_bytes:uploaded": 4_000_000,
        "ocr:pages": 8,
        "stt:seconds": 120,
        "tts:characters": 400,
        "vision:images": 6,
    }
    serialized = json.dumps(dimensions)
    assert "4242" not in serialized
    assert "PRIVATE-PROMPT" not in serialized
    assert "report.pdf" not in serialized


def test_usage_anomalies_are_observable_before_invoice_reconciliation(caplog):
    dimensions = aggregate_usage_dimensions(_events())
    anomalies = detect_usage_anomalies(
        current=dimensions,
        baseline={"ocr:pages": 2, "vision:images": 2},
        ratio_threshold=2.0,
        minimum_delta=1,
    )

    with caplog.at_level("WARNING", logger="iamina.cost"):
        emit_usage_anomaly_alerts(anomalies)

    text = "\n".join(record.getMessage() for record in caplog.records)
    assert "usage_anomaly" in text
    assert "reconciliation_gap" not in text
    assert "PRIVATE-PROMPT" not in text
    assert "patient" not in text


def test_anomaly_alert_and_reconciliation_are_aggregate_only(caplog):
    report = build_finops_audit_report(
        events=_events(),
        baseline_dimensions={
            "llm:input_tokens": 50,
            "ocr:pages": 2,
            "vision:images": 2,
            "stt:seconds": 30,
            "tts:characters": 100,
            "media_bytes:uploaded": 1_000_000,
        },
        active_users=10,
        billed_microusd=1_000,
        workload_costs_microusd={"conversation": 700, "ocr": 200},
        anomaly_ratio_threshold=2.0,
        anomaly_minimum_delta=1,
    )

    assert report["reconciliation"] == {
        "billed_microusd": 1_000,
        "explained_microusd": 900,
        "unexplained_microusd": 100,
        "ratio": 0.9,
        "billed_microusd_per_mau": 100.0,
        "floor": 0.95,
        "meets_floor": False,
    }
    metrics = {item["metric"] for item in report["anomalies"]}
    assert "llm:input_tokens" in metrics
    assert "ocr:pages" in metrics
    assert "vision:images" in metrics
    assert "stt:seconds" in metrics
    assert "media_bytes:uploaded" in metrics

    with caplog.at_level("WARNING", logger="iamina.cost"):
        emit_finops_audit_alerts(report)

    text = "\n".join(record.getMessage() for record in caplog.records)
    assert "usage_anomaly" in text
    assert "reconciliation_gap" in text
    assert "PRIVATE-PROMPT" not in text
    assert "patient" not in text
    assert "report.pdf" not in text


def test_malformed_metric_unit_fails_closed_before_alerting():
    with pytest.raises(ValueError, match="safe canonical label"):
        aggregate_usage_dimensions(
            [
                {
                    "event": "metered_usage",
                    "status": "success",
                    "modality": "ocr",
                    "unit": "patient-42@example",
                    "quantity": 1,
                }
            ]
        )
