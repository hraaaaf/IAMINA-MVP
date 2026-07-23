"""
diabetes.api.v1.analytics — Staff-only retention dashboard endpoint.

Exposes GET /api/v1/analytics/overview for internal staff use only.
Returns cohort retention rates, event funnel counts, and companion engagement KPIs.

Security: is_staff check is the first operation after auth — non-staff never
reach compute_retention_metrics().

Query params:
    module (str, optional): module_id to scope retention. Defaults to "diabetes".
        Must be a registered module — returns 404 if unknown.
"""
import logging

from ninja import Router
from ninja.errors import HttpError

from core.observability import compute_retention_metrics

logger = logging.getLogger(__name__)

router = Router(tags=["analytics"])


@router.get("/analytics/overview")
def get_overview(request, module: str = "diabetes") -> dict:
    """
    Return retention + engagement KPIs for the staff dashboard.

    Requires: request.user.is_staff == True.

    Args:
        module: module_id whose manifest.acquisition_event is used as the
                cohort acquisition anchor. Defaults to "diabetes".

    Returns: JSON object matching the shape defined in the API spec.
    """
    if not request.user.is_staff:
        raise HttpError(403, "Forbidden")

    from core.registry import ModuleRegistry

    if not ModuleRegistry.is_registered(module):
        raise HttpError(404, f"Module '{module}' not registered")

    manifest = ModuleRegistry.get(module).manifest

    try:
        metrics = compute_retention_metrics(acquisition_event=manifest.acquisition_event)
    except Exception:
        logger.exception("analytics.get_overview: compute_retention_metrics failed")
        raise HttpError(500, "Internal error")

    return {
        "retention": {
            "d1":  metrics.retention_d1,
            "d7":  metrics.retention_d7,
            "d30": metrics.retention_d30,
            "d90": metrics.retention_d90,
        },
        "cohort_ready": {
            "d1":  metrics.cohort_ready_d1,
            "d7":  metrics.cohort_ready_d7,
            "d30": metrics.cohort_ready_d30,
            "d90": metrics.cohort_ready_d90,
        },
        "funnel": {
            "session_start":  metrics.funnel_session_start,
            "log_created":    metrics.funnel_log_created,
            "chat_message":   metrics.funnel_chat_message,
            "summary_viewed": metrics.funnel_summary_viewed,
        },
        "companion_engagement": {
            "chat_per_active_patient": metrics.chat_per_active_patient,
        },
        "cohort_size": metrics.cohort_size,
        "computed_at": metrics.computed_at.isoformat() + "Z",
    }
