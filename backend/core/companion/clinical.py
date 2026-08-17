"""
core/companion/clinical.py — chassis clinical-context resolver (P4.5).

The single entry point the companion runtime uses to obtain a module's instant
DomainContext, governed longitudinal CompanionContext and offline alerts.
Resolution always goes through the active module's BaseEngine contract, keeping
the chassis condition-agnostic.
"""
import json
import logging
from dataclasses import asdict

from django.core.cache import cache

from core.contracts.companion_context import CompanionContext
from core.contracts.domain_context import DomainContext

logger = logging.getLogger(__name__)

CONTEXT_TTL = 1800  # 30 minutes — mirrors the former session_cache economy


def _key(patient_id: int, days: int, language: str) -> str:
    return f"companion:ctx:{patient_id}:{days}:{language}"


def _resolve_engine(patient_id: int):
    """Return an instance of the active module's engine for this patient, or None."""
    from core.registry import ModuleRegistry

    modules = ModuleRegistry.all()
    if not modules:
        return None
    # Single-module deployment (current): the only module is the active one.
    if len(modules) == 1:
        return modules[0].engine_class()
    # Multi-module (future): pick the engine for a module the patient activated.
    try:
        from core.models import PatientModule

        active = set(
            PatientModule.objects.filter(
                patient__patient_id=patient_id, is_active=True
            ).values_list("module_name", flat=True)
        )
    except Exception:
        logger.exception("PatientModule lookup failed for patient=%s", patient_id)
        active = set()
    for m in modules:
        if m.manifest.name in active:
            return m.engine_class()
    return None


def get_domain_context(patient_id: int, language: str = "fr", days: int = 14) -> DomainContext:
    """Cached DomainContext for the patient's active module (empty if none)."""
    raw = cache.get(_key(patient_id, days, language))
    if raw:
        try:
            return DomainContext(**json.loads(raw))
        except Exception:
            logger.exception("DomainContext cache decode failed for patient=%s", patient_id)

    engine = _resolve_engine(patient_id)
    if engine is None:
        return DomainContext.empty(language=language)

    ctx = engine.analyze(patient_id, language=language, days=days)
    try:
        cache.set(_key(patient_id, days, language), json.dumps(asdict(ctx)), timeout=CONTEXT_TTL)
    except Exception:
        logger.exception("DomainContext cache set failed for patient=%s", patient_id)
    return ctx


def get_companion_context(
    patient_id: int,
    language: str = "fr",
) -> CompanionContext:
    """Read governed longitudinal state through the active module contract."""
    engine = _resolve_engine(patient_id)
    if engine is None:
        return CompanionContext.empty(language=language)
    return engine.companion_context(patient_id, language=language)


def invalidate(patient_id: int) -> None:
    """Drop cached context after a new entry (all windows + languages)."""
    for days in (7, 14, 21, 30):
        for lang in ("fr", "ar", "ar-MA", "en"):
            cache.delete(_key(patient_id, days, lang))


def evaluate_alert(entry, patient_id: int, language: str = "fr"):
    """Offline per-entry safety gate via the active module's engine."""
    engine = _resolve_engine(patient_id)
    if engine is None:
        return None
    return engine.evaluate_alert(entry, language=language)
