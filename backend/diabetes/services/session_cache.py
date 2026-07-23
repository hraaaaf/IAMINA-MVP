"""
IAmina session context cache — RETIRED (P4.5).

Clinical context now flows through the single engine contract
(DiabetesEngine.analyze → DomainContext) and is cached by
core/companion/clinical.py. The former get_session_context()/SessionContext
build path has been removed.

This module remains only as the invalidation entry point that diabetes log/
profile writes call; it delegates to the chassis clinical cache.
"""


def invalidate(patient_id: int) -> None:
    """Drop the patient's cached clinical context after a data change."""
    from core.companion.clinical import invalidate as _chassis_invalidate

    _chassis_invalidate(patient_id)
