"""Diabetes-owned retention declarations for confirmed document data."""

from __future__ import annotations

from core.retention import RetentionClass, RetentionPolicy

LAB_REPORT_RAW_TEXT_POLICY = RetentionPolicy(
    storage_key="diabetes.LabReport.raw_text",
    retention_class=RetentionClass.GOVERNED_EVIDENCE,
    policy_basis=(
        "legacy audit-trail text; destructive lifecycle pending explicit "
        "product/legal/CNDP review"
    ),
    human_gate_required=True,
)

LAB_REPORT_STRUCTURED_POLICY = RetentionPolicy(
    storage_key="diabetes.LabReport.structured_fields",
    retention_class=RetentionClass.STRUCTURED_VERIFIED_FACTS,
    policy_basis="user-confirmed structured health record",
    human_gate_required=True,
)

DOCUMENT_RETENTION_POLICIES = (
    LAB_REPORT_RAW_TEXT_POLICY,
    LAB_REPORT_STRUCTURED_POLICY,
)
