"""V1-03 privacy gate for raw patient media leaving the IAmina backend.

Consent and an approved processor contract are necessary but do not prove
a patient-origin recording, photo or document contains no patient context.
No generic/opaque transport contract is currently certified for raw media.
Keep network media egress closed until a separately reviewed replacement is
implemented; an environment switch must not silently reopen this gate.
"""
from __future__ import annotations

from core.ai_processor_policy import AIProcessorPolicyDenied

def assert_v1_external_media_egress_denied(modality: str) -> None:
    """Reject patient-origin media at the irreversible external call boundary."""
    # This module is the non-text network boundary: all modalities, including
    # future ones, remain denied until a separately certified allowlist exists.
    raise AIProcessorPolicyDenied(
        "V1-03 external raw patient media is disabled pending a certified "
        "privacy-preserving media contract"
    )
