"""Truth provenance contract for IAmina companion data.

The companion must never collapse observations, patient claims, deterministic
clinical derivations and generative-model inferences into one untyped memory.
This module gives the shared chassis a small executable vocabulary for the
provenance and authority of information used by IAmina.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TruthKind(str, Enum):
    """Origin/epistemic class of a piece of information."""

    OBSERVED_FACT = "observed_fact"
    USER_CLAIM = "user_claim"
    DETERMINISTIC_DERIVATION = "deterministic_derivation"
    PREFERENCE = "preference"
    CONVERSATIONAL_STATE = "conversational_state"
    MODEL_INFERENCE = "model_inference"


_PATIENT_FACT_PERSISTABLE = frozenset(
    {
        TruthKind.OBSERVED_FACT,
        TruthKind.USER_CLAIM,
        TruthKind.PREFERENCE,
    }
)

_CLINICAL_AUTHORITY = frozenset(
    {
        TruthKind.OBSERVED_FACT,
        TruthKind.DETERMINISTIC_DERIVATION,
    }
)


@dataclass(frozen=True)
class TruthRecord:
    """A value paired with explicit provenance and a stable source label.

    `source` is intentionally a plain identifier such as ``journal.log`` or
    ``diabetes.sql_analytics``. It must not contain patient PHI.
    """

    key: str
    value: Any
    kind: TruthKind
    source: str

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise ValueError("truth record key is required")
        if not self.source or not self.source.strip():
            raise ValueError("truth record source is required")

    @property
    def may_persist_as_patient_fact(self) -> bool:
        """Whether this item may enter a patient-fact store without reclassification."""

        return self.kind in _PATIENT_FACT_PERSISTABLE

    @property
    def may_drive_clinical_decision(self) -> bool:
        """Whether this provenance class may be authoritative for clinical logic.

        A USER_CLAIM can be stored and displayed as a claim, but it must not be
        silently upgraded into validated clinical truth. MODEL_INFERENCE and
        CONVERSATIONAL_STATE are never clinical decision authority.
        """

        return self.kind in _CLINICAL_AUTHORITY

    def assert_patient_fact_persistence_allowed(self) -> None:
        if not self.may_persist_as_patient_fact:
            raise ValueError(
                f"{self.kind.value} cannot be persisted as a patient fact without "
                "explicit reclassification from an authoritative source"
            )

    def assert_clinical_authority(self) -> None:
        if not self.may_drive_clinical_decision:
            raise ValueError(f"{self.kind.value} is not clinical decision authority")
