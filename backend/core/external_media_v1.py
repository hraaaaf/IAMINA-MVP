"""V1-03 privacy gate for raw patient media leaving the IAmina backend.

Consent and an approved processor contract are necessary but do not prove
a patient-origin recording, photo or document contains no patient context.
No generic/opaque transport contract is currently certified for raw media.
Keep network media egress closed until a separately reviewed replacement is
implemented; an environment switch must not silently reopen this gate.
"""
from __future__ import annotations

from core.ai_egress import AUDIO, DOCUMENT, IMAGE
from core.ai_processor_policy import AIProcessorPolicyDenied

_PATIENT_MEDIA_MODALITIES = frozenset({AUDIO, IMAGE, DOCUMENT})


def assert_v1_external_media_egress_denied(modality: str) -> None:
    """Reject patient-origin media at the irreversible external call boundary."""
    if modality in _PATIENT_MEDIA_MODALITIES:
        raise AIProcessorPolicyDenied(
            "V1-03 external raw patient media is disabled pending a certified "
            "privacy-preserving media contract"
        )
