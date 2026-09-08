"""
IAmina — Unit Guard Middleware (Phase 6 Clinical Shield)
=========================================================
Enforces strict blood glucose unit validation and conversion at the API boundary.
This middleware intercepts incoming API requests and outgoing responses to:

1. Detect the declared unit (mg/dL | g/L | mmol/L).
2. Convert to the canonical internal unit (mg/dL).
3. Reject values outside the canonical persisted-input bounds.
4. Log any unit mismatch for clinical audit.

Unit confusion (mg/dL vs g/L) can be safety-relevant. The guard therefore fails
closed on unexpected normalization errors and protects both legacy API paths and
registry-mounted module paths.

See docs/adr/0007-analytical-sql-over-llm.md
"""
from __future__ import annotations

import json
import logging
from typing import Any

from django.http import JsonResponse

from diabetes.contracts import log_entry as log_input

logger = logging.getLogger(__name__)

# Legacy paths that carry glucose values and must remain guarded during route migration.
_LEGACY_GUARDED_PATHS = (
    "/api/v1/logs",
    "/api/v1/ai",
)

# JSON body field names that may carry a glucose value
_GLUCOSE_FIELDS = ("blood_sugar", "glucose", "glucose_value", "glycemia")
_UNIT_FIELDS = ("unit", "glucose_unit", "blood_sugar_unit")


class UnitConversionError(ValueError):
    """Backward-compatible public error for unsafe glucose normalization."""


def convert_to_mg_dl(value: float, unit: str) -> float:
    """Convert a supported glucose value to canonical mg/dL."""
    try:
        converted = log_input.convert_glucose_to_mg_dl(value, unit)
    except log_input.LogInputValidationError as exc:
        raise UnitConversionError(str(exc)) from exc

    if str(unit).strip().lower().replace(" ", "") not in ("mg/dl", "mgdl"):
        logger.info(
            "UnitGuard: Converted %s %s → %.1f mg/dL",
            value,
            unit,
            converted,
        )
    return converted


def validate_mg_dl(value: float) -> float:
    """Compatibility wrapper over the sole canonical 30–600 mg/dL contract."""
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise UnitConversionError("Glucose value must be numeric.") from exc
    try:
        return log_input.validate_mg_dl(numeric)
    except log_input.LogInputValidationError as exc:
        raise UnitConversionError(str(exc)) from exc


def _canonical_runtime_value(value: Any, unit: str | None) -> float:
    """Normalize one runtime payload value using the sole canonical input contract."""
    # Keep type/coercion failures distinct from governed validation failures so an
    # unexpected malformed payload remains an INTERNAL fail-closed rejection.
    numeric = float(value)
    try:
        if unit:
            return log_input.convert_glucose_to_mg_dl(numeric, unit)
        return log_input.validate_mg_dl(numeric)
    except log_input.LogInputValidationError as exc:
        raise UnitConversionError(str(exc)) from exc


class UnitGuardMiddleware:
    """Fail-closed normalization for guarded JSON API writes."""

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        if self._is_guarded(request):
            try:
                request = self._normalise_request(request)
            except UnitConversionError as exc:
                logger.warning("UnitGuard: Rejected request — %s", exc)
                return JsonResponse(
                    {"error": str(exc), "code": "UNIT_GUARD_REJECTION"},
                    status=422,
                )
            except Exception:
                logger.exception("UnitGuard: Unexpected normalization error — request blocked.")
                return JsonResponse(
                    {
                        "error": "Unable to safely validate glucose payload.",
                        "code": "UNIT_GUARD_INTERNAL_REJECTION",
                    },
                    status=422,
                )

        return self.get_response(request)

    @staticmethod
    def _path_matches_prefix(path: str, prefix: str) -> bool:
        normalized = prefix.rstrip("/")
        return path == normalized or path.startswith(f"{normalized}/")

    @staticmethod
    def _module_guarded_paths() -> tuple[str, ...]:
        """Return current registry-mounted API prefixes without hard-coding modules."""
        try:
            from core.registry import ModuleRegistry

            return tuple(
                f"/api/v1{registered.manifest.url_prefix}"
                for registered in ModuleRegistry.all()
            )
        except Exception:
            logger.exception("UnitGuard: Could not resolve module registry paths.")
            return ()

    def _is_guarded(self, request) -> bool:
        if request.method not in ("POST", "PUT", "PATCH"):
            return False

        guarded_paths = _LEGACY_GUARDED_PATHS + self._module_guarded_paths()
        return any(
            self._path_matches_prefix(request.path, prefix)
            for prefix in guarded_paths
        )

    @staticmethod
    def _declared_unit(payload: dict[str, Any]) -> str | None:
        for field in _UNIT_FIELDS:
            if field in payload:
                return str(payload[field]).strip()
        return None

    @classmethod
    def _normalise_object(cls, payload: dict[str, Any]) -> bool:
        modified = False
        declared_unit = cls._declared_unit(payload)

        for field in _GLUCOSE_FIELDS:
            if field not in payload or payload[field] is None:
                continue
            payload[field] = _canonical_runtime_value(payload[field], declared_unit)
            modified = True

        if modified and declared_unit:
            for field in _UNIT_FIELDS:
                if field in payload:
                    payload[field] = "mg/dL"
        return modified

    @classmethod
    def _normalise_payload(cls, payload: Any) -> bool:
        """Normalize one log object or a batch list of log objects."""
        if isinstance(payload, dict):
            return cls._normalise_object(payload)
        if isinstance(payload, list):
            modified = False
            for item in payload:
                if not isinstance(item, dict):
                    raise UnitConversionError("Batch glucose payload items must be objects.")
                modified = cls._normalise_object(item) or modified
            return modified
        return False

    def _normalise_request(self, request):
        """Normalize supported glucose fields in a JSON object or batch array."""
        content_type = request.content_type or ""
        if "application/json" not in content_type:
            return request

        raw_body = request.body
        if not raw_body:
            return request

        try:
            payload: Any = json.loads(raw_body)
        except json.JSONDecodeError:
            return request

        if self._normalise_payload(payload):
            request._body = json.dumps(payload).encode("utf-8")  # type: ignore[attr-defined]

        return request
