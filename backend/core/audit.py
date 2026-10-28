"""
core/audit.py — RGPD audit port.

The chassis records consent/account audit events without importing a module's
AuditLog model. The active module registers a sink at startup
(DiabetesConfig.ready()); core/api/v1/account.py records through record_audit().
Keeps core/ free of diabetes.* (import-linter boundary). The audit table stays
in the module for now; relocation to core is deferred (cf. P7.5).

If no sink is registered the call is a safe no-op.
"""
import logging

logger = logging.getLogger(__name__)

# Sink signature: (patient, action: str, request=None, **metadata) -> None
_audit_sink = None


def register_audit_sink(sink) -> None:
    """Register the active module's audit sink (called in AppConfig.ready())."""
    global _audit_sink
    _audit_sink = sink


def record_audit(patient, action: str, request=None, **metadata) -> None:
    """Record an audit event via the registered sink; no-op if none registered."""
    if _audit_sink is None:
        return
    try:
        _audit_sink(patient, action, request, **metadata)
    except Exception:
        logger.exception("audit sink failed for action=%s", action)


def record_audit_required(patient, action: str, request=None, **metadata) -> None:
    """Fail closed if a mandatory compliance audit cannot be persisted.

    Unlike the best-effort port, erasure must not commit successfully if its
    audit sink is missing or raises. Invoke inside the same DB transaction as
    the audited operation; this cannot make external providers transactional.
    """
    if _audit_sink is None:
        raise RuntimeError("mandatory audit sink unavailable")
    _audit_sink(patient, action, request, **metadata)
