"""Patient-scoped portability export for confirmed diabetes document records."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User

from diabetes.models import LabReport

SCHEMA_VERSION = "diabetes.documents.v1"


def build_document_portability_export(patient: User) -> dict[str, Any]:
    """Return a deterministic JSON-safe export without original binary media or transport secrets."""
    reports = LabReport.objects.filter(patient=patient).order_by("created_at", "pk")
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "diabetes.documents",
        "original_media_retained": False,
        "reports": [_serialize_report(report) for report in reports],
    }


def _serialize_report(report: LabReport) -> dict[str, Any]:
    return {
        "id": report.pk,
        "document_type": report.document_type,
        "source_format": report.source_format,
        "report_date": report.report_date.isoformat() if report.report_date else None,
        "structured_values": {
            "hba1c_pct": report.hba1c_pct,
            "fasting_glucose_mgdl": report.fasting_glucose_mgdl,
            "total_cholesterol_mgdl": report.total_cholesterol_mgdl,
            "hdl_mgdl": report.hdl_mgdl,
            "ldl_mgdl": report.ldl_mgdl,
            "triglycerides_mgdl": report.triglycerides_mgdl,
            "creatinine_umol": report.creatinine_umol,
        },
        "glucose_readings_imported": report.glucose_readings_imported,
        "confidence": report.confidence,
        "clinical_notes": report.clinical_notes,
        "retained_source": {"raw_text": report.raw_text},
        "created_at": report.created_at.isoformat(),
    }
