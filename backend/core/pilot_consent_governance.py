"""Pilot consent matrix and processor/subprocessor readiness contract.

This module is operational evidence plumbing, not legal approval. Patient consent,
CNDP treatment authorization, foreign-transfer authorization and processor approval
are independent gates. Missing or stale evidence always fails closed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from types import MappingProxyType

from core.ai_processor_policy import (
    APPROVED,
    registered_processor_policies,
)

PENDING = "pending"
NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class ConsentRequirement:
    purpose: str
    modality: str
    patient_notice_required: bool
    base_ai_consent_required: bool
    raw_media_consent_required: bool
    health_data_authorization_required: bool
    foreign_transfer_gate_required: bool
    processor_approval_required: bool

    def validate(self) -> None:
        if not self.purpose.strip() or not self.modality.strip():
            raise ValueError("consent requirement purpose and modality are required")
        if self.modality in {"audio", "image", "document"} and not self.raw_media_consent_required:
            raise ValueError(
                f"raw-media purpose {self.purpose}/{self.modality} lacks granular consent"
            )
        if self.processor_approval_required and not self.base_ai_consent_required:
            raise ValueError(
                f"external AI purpose {self.purpose}/{self.modality} lacks base AI consent"
            )


@dataclass(frozen=True, slots=True)
class ApprovalEvidence:
    status: str
    reference: str
    owner_role: str
    reviewed_on: date | None = None
    review_due_on: date | None = None

    def validate(self, *, label: str, today: date) -> None:
        if self.status not in {APPROVED, PENDING, NOT_APPLICABLE}:
            raise ValueError(f"{label} has invalid evidence status")
        if not self.owner_role.strip():
            raise ValueError(f"{label} has no accountable owner role")
        if self.status == APPROVED:
            if not self.reference.strip():
                raise ValueError(f"{label} is approved without an evidence reference")
            if self.reviewed_on is None or self.review_due_on is None:
                raise ValueError(f"{label} is approved without review dates")
            if self.reviewed_on > today:
                raise ValueError(f"{label} review date is in the future")
            if self.review_due_on < today:
                raise ValueError(f"{label} evidence is stale")
        elif self.status == NOT_APPLICABLE and not self.reference.strip():
            raise ValueError(f"{label} is not-applicable without rationale")


@dataclass(frozen=True, slots=True)
class ProcessorEvidenceRecord:
    provider: str
    external_egress: bool
    processor_identity: ApprovalEvidence
    contract_dpa: ApprovalEvidence
    subprocessor_register: ApprovalEvidence
    processing_regions: ApprovalEvidence
    retention_and_deletion: ApprovalEvidence
    training_use: ApprovalEvidence
    security_review: ApprovalEvidence
    privacy_review: ApprovalEvidence
    cndp_health_processing_authorization: ApprovalEvidence
    cndp_foreign_transfer_authorization: ApprovalEvidence

    def validate(self, *, today: date) -> None:
        if not self.provider.strip():
            raise ValueError("processor evidence provider is required")
        evidence = self._evidence_fields()
        for name, item in evidence.items():
            item.validate(label=f"{self.provider}.{name}", today=today)

        if self.external_egress:
            invalid = [
                name
                for name, item in evidence.items()
                if item.status != APPROVED
            ]
            if not invalid:
                return
            # Pending evidence is valid for preparation, but cannot be presented as
            # production approval. readiness_payload reports these blockers.
            return

        for name, item in evidence.items():
            if name == "processor_identity":
                if item.status != APPROVED:
                    raise ValueError(
                        f"local provider {self.provider} lacks approved identity evidence"
                    )
            elif item.status != NOT_APPLICABLE:
                raise ValueError(
                    f"local provider {self.provider} must mark {name} not applicable"
                )

    def _evidence_fields(self) -> dict[str, ApprovalEvidence]:
        return {
            "processor_identity": self.processor_identity,
            "contract_dpa": self.contract_dpa,
            "subprocessor_register": self.subprocessor_register,
            "processing_regions": self.processing_regions,
            "retention_and_deletion": self.retention_and_deletion,
            "training_use": self.training_use,
            "security_review": self.security_review,
            "privacy_review": self.privacy_review,
            "cndp_health_processing_authorization": self.cndp_health_processing_authorization,
            "cndp_foreign_transfer_authorization": self.cndp_foreign_transfer_authorization,
        }

    def blockers(self, *, today: date) -> tuple[str, ...]:
        if not self.external_egress:
            return ()
        blockers: list[str] = []
        for name, item in self._evidence_fields().items():
            if item.status != APPROVED:
                blockers.append(f"{self.provider}.{name}:{item.status}")
            elif item.review_due_on is not None and item.review_due_on < today:
                blockers.append(f"{self.provider}.{name}:stale")
        return tuple(blockers)


_ALL_PURPOSE_MODALITIES = frozenset(
    {
        (purpose, modality)
        for policy in registered_processor_policies().values()
        for purpose in policy.allowed_purposes
        for modality in policy.allowed_modalities
    }
)


def _requirement(purpose: str, modality: str) -> ConsentRequirement:
    raw_media = modality in {"audio", "image", "document"}
    return ConsentRequirement(
        purpose=purpose,
        modality=modality,
        patient_notice_required=True,
        base_ai_consent_required=True,
        raw_media_consent_required=raw_media,
        health_data_authorization_required=True,
        foreign_transfer_gate_required=True,
        processor_approval_required=True,
    )


CONSENT_MATRIX = tuple(
    _requirement(purpose, modality)
    for purpose, modality in sorted(_ALL_PURPOSE_MODALITIES)
)


def _pending(reference: str, owner_role: str) -> ApprovalEvidence:
    return ApprovalEvidence(
        status=PENDING,
        reference=reference,
        owner_role=owner_role,
    )


def _not_applicable(reason: str) -> ApprovalEvidence:
    return ApprovalEvidence(
        status=NOT_APPLICABLE,
        reference=reason,
        owner_role="IAmina Privacy Owner",
    )


def _local_record(provider: str) -> ProcessorEvidenceRecord:
    identity = ApprovalEvidence(
        status=APPROVED,
        reference="IAmina local runtime; no external patient-data egress",
        owner_role="IAmina Security Owner",
        reviewed_on=date(2026, 8, 4),
        review_due_on=date(2026, 11, 4),
    )
    na = _not_applicable("No external processor or foreign transfer")
    return ProcessorEvidenceRecord(
        provider=provider,
        external_egress=False,
        processor_identity=identity,
        contract_dpa=na,
        subprocessor_register=na,
        processing_regions=na,
        retention_and_deletion=na,
        training_use=na,
        security_review=na,
        privacy_review=na,
        cndp_health_processing_authorization=na,
        cndp_foreign_transfer_authorization=na,
    )


def _network_record(
    provider: str,
    *,
    processor_reference: str,
    subprocessor_reference: str,
    residency_reference: str,
) -> ProcessorEvidenceRecord:
    return ProcessorEvidenceRecord(
        provider=provider,
        external_egress=True,
        processor_identity=_pending(processor_reference, "IAmina Privacy Owner"),
        contract_dpa=_pending(
            "Executed account-specific DPA and applicable service terms required",
            "IAmina Legal/Privacy Owner",
        ),
        subprocessor_register=_pending(
            subprocessor_reference,
            "IAmina Privacy Owner",
        ),
        processing_regions=_pending(
            residency_reference,
            "IAmina Architecture and Privacy Owners",
        ),
        retention_and_deletion=_pending(
            "Account/model-specific retention and deletion evidence required",
            "IAmina Privacy Owner",
        ),
        training_use=_pending(
            "Account/model-specific no-training evidence required",
            "IAmina Privacy Owner",
        ),
        security_review=_pending(
            "Completed vendor and deployment security review required",
            "IAmina Security Owner",
        ),
        privacy_review=_pending(
            "Completed deployment-specific privacy review required",
            "IAmina Privacy Owner",
        ),
        cndp_health_processing_authorization=_pending(
            "CNDP authorization reference for health-data processing required",
            "IAmina Data Controller",
        ),
        cndp_foreign_transfer_authorization=_pending(
            "CNDP foreign-transfer authorization or documented applicable basis required",
            "IAmina Data Controller",
        ),
    )


PROCESSOR_EVIDENCE = MappingProxyType(
    {
        "gemini": _network_record(
            "gemini",
            processor_reference="Google Cloud account and contracting entity must be confirmed",
            subprocessor_reference="Google Cloud Platform Subprocessors — current official list",
            residency_reference="Google Cloud data-residency terms and selected deployment region",
        ),
        "kimi": _network_record(
            "kimi",
            processor_reference="Kimi endpoint operator and contracting entity not approved",
            subprocessor_reference="No approved official subprocessor evidence on file",
            residency_reference="No approved processing-region evidence on file",
        ),
        "claude": _network_record(
            "claude",
            processor_reference="Anthropic contracting entity must be confirmed",
            subprocessor_reference="Current official Anthropic subprocessor evidence required",
            residency_reference="Account/model-specific processing-region evidence required",
        ),
        "fallback": _local_record("fallback"),
        "quota-exhausted": _local_record("quota-exhausted"),
    }
)


def validate_consent_governance(*, today: date | None = None) -> None:
    """Validate structural completeness without pretending pending evidence is approved."""
    current = today or date.today()
    matrix_keys: set[tuple[str, str]] = set()
    for requirement in CONSENT_MATRIX:
        requirement.validate()
        key = (requirement.purpose, requirement.modality)
        if key in matrix_keys:
            raise ValueError(f"duplicate consent matrix entry: {key}")
        matrix_keys.add(key)

    if matrix_keys != set(_ALL_PURPOSE_MODALITIES):
        missing = sorted(_ALL_PURPOSE_MODALITIES - matrix_keys)
        extra = sorted(matrix_keys - _ALL_PURPOSE_MODALITIES)
        raise ValueError(f"consent matrix drift; missing={missing}, extra={extra}")

    runtime_policies = registered_processor_policies()
    if set(PROCESSOR_EVIDENCE) != set(runtime_policies):
        missing = sorted(set(runtime_policies) - set(PROCESSOR_EVIDENCE))
        extra = sorted(set(PROCESSOR_EVIDENCE) - set(runtime_policies))
        raise ValueError(f"processor evidence drift; missing={missing}, extra={extra}")

    for provider, record in PROCESSOR_EVIDENCE.items():
        record.validate(today=current)
        runtime_policy = runtime_policies[provider]
        if runtime_policy.external_egress != record.external_egress:
            raise ValueError(f"processor egress mismatch for {provider}")
        if runtime_policy.external_egress and runtime_policy.status == APPROVED:
            blockers = record.blockers(today=current)
            if blockers:
                raise ValueError(
                    f"runtime provider {provider} is approved with governance blockers: {blockers}"
                )


def consent_governance_payload(
    *,
    today: date | None = None,
    require_approved: bool = False,
) -> dict[str, object]:
    """Return a deterministic readiness report and optionally enforce pilot approval."""
    current = today or date.today()
    validate_consent_governance(today=current)

    provider_rows: list[dict[str, object]] = []
    all_blockers: list[str] = []
    for provider in sorted(PROCESSOR_EVIDENCE):
        record = PROCESSOR_EVIDENCE[provider]
        blockers = record.blockers(today=current)
        all_blockers.extend(blockers)
        provider_rows.append(
            {
                "provider": provider,
                "external_egress": record.external_egress,
                "runtime_status": registered_processor_policies()[provider].status,
                "governance_status": "approved" if not blockers else "pending",
                "blockers": list(blockers),
                "evidence": {
                    name: {
                        **asdict(item),
                        "reviewed_on": item.reviewed_on.isoformat() if item.reviewed_on else None,
                        "review_due_on": item.review_due_on.isoformat()
                        if item.review_due_on
                        else None,
                    }
                    for name, item in record._evidence_fields().items()
                },
            }
        )

    if require_approved and all_blockers:
        raise ValueError(
            "pilot consent/processor governance is not approved: "
            + ", ".join(all_blockers)
        )

    return {
        "schema_version": "2026-08-04.1",
        "as_of": current.isoformat(),
        "status": "approved" if not all_blockers else "pending_external_approval",
        "consent_matrix": [asdict(item) for item in CONSENT_MATRIX],
        "processors": provider_rows,
        "blockers": sorted(all_blockers),
        "non_claim": (
            "Structural readiness is not legal, CNDP, processor, security or privacy approval."
        ),
    }
