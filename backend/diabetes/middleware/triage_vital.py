"""
DEPRECATED — diabetes.middleware.triage_vital
==============================================
This module has been relocated to ``core.middleware.triage_vital`` as part of
the P1.1 Triage Path Registry migration (2026-06-04).

Update your imports:

    # Old (broken):
    from diabetes.middleware.triage_vital import TriageVitalMiddleware

    # New (correct):
    from core.middleware.triage_vital import TriageVitalMiddleware

Settings MIDDLEWARE entry must be:
    'core.middleware.triage_vital.TriageVitalMiddleware'
"""

raise ImportError(
    "diabetes.middleware.triage_vital has moved to core.middleware.triage_vital. "
    "Update your imports and settings.py MIDDLEWARE entry to use "
    "'core.middleware.triage_vital.TriageVitalMiddleware'."
)
