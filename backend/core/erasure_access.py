"""Deny all known identity paths after the durable erasure claim exists.

No raw Firebase UID, personal identifier, or exception detail leaves this guard.
The unique indexed patient snapshot prevents a completed deletion from silently
authenticating a later identity that reused the same numeric User primary key.
"""
from core.models.erasure_attempt import ErasureAttempt


def erasure_blocks_access(user) -> bool:
    patient_id = getattr(user, "pk", None)
    if isinstance(patient_id, bool) or not isinstance(patient_id, int):
        return False
    return ErasureAttempt.objects.filter(patient_id_snapshot=patient_id).exists()
