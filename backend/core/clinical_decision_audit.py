"""PHI-safe audit trail for governed clinical advice decisions."""
from __future__ import annotations

from hashlib import sha256

from django.contrib.auth.models import User

from core.contracts.advice_decision import AdviceDecision
from core.models import AuditLog

AUDIT_SCHEMA_VERSION = "clinical-advice-audit.v1"
_ALLOWED_VERIFIER_STATUSES = frozenset({"passed", "rejected"})


def clinical_decision_audit_metadata(
    *,
    decision: AdviceDecision,
    verifier_status: str,
    final_reply: str,
) -> dict[str, object]:
    """Build reconstructible, content-free clinical decision audit metadata."""
    if not isinstance(decision, AdviceDecision):
        raise ValueError("decision must be an AdviceDecision")
    if verifier_status not in _ALLOWED_VERIFIER_STATUSES:
        raise ValueError("unsupported verifier_status")
    if not isinstance(final_reply, str) or not final_reply.strip():
        raise ValueError("final_reply is required")

    required = tuple(decision.required_facts)
    missing = set(decision.missing_facts)
    used = tuple(key for key in required if key not in missing)

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "intent": decision.intent,
        "authority_level": decision.authority_level.value,
        "disposition": decision.decision.value,
        "rule_id": decision.rule_id,
        "rule_version": decision.rule_version,
        "allowed_actions": list(decision.allowed_actions),
        "forbidden_actions": list(decision.forbidden_actions),
        "constraints_applied": {
            "allowed_actions": list(decision.allowed_actions),
            "forbidden_actions": list(decision.forbidden_actions),
            "limitations": list(decision.limitations),
        },
        "required_fact_keys": list(required),
        "used_fact_keys": list(used),
        "missing_fact_keys": list(decision.missing_facts),
        "evidence_refs": list(decision.evidence_refs),
        "limitations": list(decision.limitations),
        "issued_by": decision.issued_by.value,
        "verifier_status": verifier_status,
        "final_reply_sha256": sha256(final_reply.strip().encode("utf-8")).hexdigest(),
    }


def clinician_audit_detail(entry: AuditLog) -> dict[str, object]:
    """Return the complete PHI-safe decision basis for clinician review."""
    if not isinstance(entry, AuditLog):
        raise ValueError("entry must be an AuditLog")
    if entry.resource_type != "ClinicalAdviceDecision":
        raise ValueError("not a clinical advice audit entry")
    metadata = entry.metadata
    if not isinstance(metadata, dict):
        raise ValueError("clinical advice audit metadata must be an object")
    if metadata.get("schema_version") != AUDIT_SCHEMA_VERSION:
        raise ValueError("unsupported clinical advice audit schema")
    required = {
        "rule_id",
        "rule_version",
        "authority_level",
        "disposition",
        "used_fact_keys",
        "missing_fact_keys",
        "constraints_applied",
        "verifier_status",
        "final_reply_sha256",
    }
    missing = sorted(required - set(metadata))
    if missing:
        raise ValueError("incomplete clinical advice audit: " + ", ".join(missing))
    return dict(metadata)


def record_clinical_decision_audit(
    *,
    patient,
    decision: AdviceDecision,
    verifier_status: str,
    final_reply: str,
) -> AuditLog | None:
    """Persist one governed decision audit without copying patient/reply content."""
    if patient is not None and not isinstance(patient, User):
        return None

    actor = patient if isinstance(patient, User) and patient.pk is not None else None
    metadata = clinical_decision_audit_metadata(
        decision=decision,
        verifier_status=verifier_status,
        final_reply=final_reply,
    )
    return AuditLog.objects.create(
        actor=actor,
        action="create",
        resource_type="ClinicalAdviceDecision",
        resource_id=f"{decision.rule_id}@{decision.rule_version}",
        metadata=metadata,
    )


__all__ = [
    "AUDIT_SCHEMA_VERSION",
    "clinical_decision_audit_metadata",
    "clinician_audit_detail",
    "record_clinical_decision_audit",
]
