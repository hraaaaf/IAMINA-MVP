"""Retention policy for temporary document extraction batches."""

from __future__ import annotations

from core.retention import RetentionClass, RetentionPolicy

PENDING_EXTRACTION_POLICY = RetentionPolicy(
    storage_key="media.documents.pending_extraction",
    retention_class=RetentionClass.TRANSIENT_EXTRACTION,
    policy_basis="temporary user review before explicit document confirmation",
    destructive_ttl_seconds=3600,
)
