"""
IAmina — Unit Guard Middleware (Phase 6 Clinical Shield)
=========================================================
Enforces strict blood glucose unit validation and conversion at the API boundary.
This middleware intercepts incoming API requests and outgoing responses to:

1. Detect the declared unit (mg/dL | g/L | mmol/L).
2. Convert to the canonical internal unit (mg/dL).
3. Reject values outside physiologically plausible bounds.
4. Log any unit mismatch for clinical audit.

Unit confusion (mg/dL vs g/L) is a documented source of dangerous dosing errors.
The guard therefore fails closed on unexpected normalization errors and protects
both legacy API paths and registry-mounted module paths.

See docs/adr/0007-analytical-sql-over-llm.md
"""
from __future__ import annotations

import json
import logging
from typing import Any

from django.http import JsonResponse

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# 1. CONVERSION CONSTANTS & BOUNDS
# ──────────────────────────────────────────────────────────────

# Physiologically plausible blood glucose range in mg/dL
# Source: ADA 2025 clinical standards
_MIN_GLUCOSE_MG_DL = 20.0
_MAX_GLUCOSE_MG_DL = 700.0

# Conversion factors TO mg/dL
_CONVERSION_FACTORS: dict[str, float] = {
    "mg/dl": 1.0,
    "mgdl": 1.0,
    "g/l": 100.0,  # 1 g/L = 100 mg/dL
    "gl": 100.0,
    "mmol/l": 18.016,  # 1 mmol/L = 18.016 mg/dL
    "mmol": 18.016,
    "mmoll": 18.016,
}

# Legacy paths that carry glucose values and must remain guarded during route migration.
_LEGACY_GUARDED_PATHS = (
    "/api/v1/logs",
    "/api/v1/ai",
)

# JSON body field names that may carry a glucose value
_GLUCOSE_FIELDS = ("blood_sugar", "glucose", "glucose_value", "glycemia")
_UNIT_FIELDS = ("unit", "glucose_unit", "blood_sugar_unit")


# ──────────────────────────────────────────────────────────────
# 2. CONVERSION LOGIC
# ──────────────────────────────────────────────────────────────

class UnitConversionError(ValueError):
    """Raised when a glucose value cannot be safely normalised."""


def convert_to_mg_dl(value: float, unit: str) -> float:
    """
    Convert a glucose value to mg/dL.

    Args:
        value: Numeric glucose measurement.
        unit: Source unit string (case-insensitive).

    Returns:
        Value in mg/dL, rounded to 1 decimal.

    Raises:
        UnitConversionError: If the unit is unknown or the result is physiologically implausible.
    """
    normalised_unit = unit.lower().replace(" ", "").replace("-", "")
    factor = _CONVERSION_FACTORS.get(normalised_unit)

    if factor is None:
        raise UnitConversionError(
            f"Unknown glucose unit: '{unit}'. Accepted: mg/dL, g/L, mmol/L."
        )

    converted = round(value * factor, 1)

    if not (_MIN_GLUCOSE_MG_DL <= converted <= _MAX_GLUCOSE_MG_DL):
        raise UnitConversionError(
            f"Glucose value {converted} mg/dL (converted from {value} {unit}) is outside "
            f"physiologically plausible range [{_MIN_GLUCOSE_MG_DL}–{_MAX_GLUCOSE_MG_DL}] mg/dL. "
            "Submission rejected for patient safety."
        )

    if unit.lower() not in ("mg/dl", "mgdl"):
        logger.info(
            "UnitGuard: Converted %.1f %s → %.1f mg/dL",
            value,
            unit,
            converted,
        )

    return converted


def validate_mg_dl(value: float) -> float:
    """
    Validate a value already in mg/dL for physiological plausibility.

    Raises:
        UnitConversionError: If the value is outside safe bounds.
    """
    if not (_MIN_GLUCOSE_MG_DL <= float(value) <= _MAX_GLUCOSE_MG_DL):
        raise UnitConversionError(
            f"Glucose value {value} mg/dL is outside physiologically safe range "
            f"[{_MIN_GLUCOSE_MG_DL}–{_MAX_GLUCOSE_MG_DL}] mg/dL."
        )
    return float(value)


# ──────────────────────────────────────────────────────────────
# 3. DJANGO MIDDLEWARE
# ──────────────────────────────────────────────────────────────

class UnitGuardMiddleware:
    """
    Django WSGI middleware that intercepts guarded API endpoints
    and enforces glucose unit validation on JSON request bodies.

    Activation: add 'diabetes.middleware.unit_guard.UnitGuardMiddleware'
    to MIDDLEWARE in settings.py AFTER SecurityMiddleware.

    Only POST/PUT/PATCH requests with a JSON body are inspected.
    GET requests and non-guarded paths are passed through unchanged.
    """

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
                # Safety boundary: an unexpected normalization failure must never
                # allow an unvalidated glucose payload to continue downstream.
                logger.exception("UnitGuard: Unexpected normalization error — request blocked.")
                return JsonResponse(
                    {
                        "error": "Unable to safely validate glucose payload.",
                        "code": "UNIT_GUARD_INTERNAL_REJECTION",
                    },
                    status=422,
                )

        return self.get_response(request)

    # ── private ──

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
            # Registry lookup failure must not remove protection from legacy paths.
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

    def _normalise_request(self, request):
        """
        Reads the JSON body, detects glucose fields, converts units,
        and writes a normalised body back onto the request object.
        """
        content_type = request.content_type or ""
        if "application/json" not in content_type:
            return request

        raw_body = request.body
        if not raw_body:
            return request

        try:
            payload: dict[str, Any] = json.loads(raw_body)
        except json.JSONDecodeError:
            return request  # malformed JSON handled by Ninja validators

        modified = False

        # Detect declared unit
        declared_unit = None
        for field in _UNIT_FIELDS:
            if field in payload:
                declared_unit = str(payload[field]).strip()
                break

        # Normalise glucose fields
        for field in _GLUCOSE_FIELDS:
            if field in payload and payload[field] is not None:
                raw_value = float(payload[field])
                if declared_unit and declared_unit.lower() not in ("mg/dl", "mgdl"):
                    payload[field] = convert_to_mg_dl(raw_value, declared_unit)
                else:
                    payload[field] = validate_mg_dl(raw_value)
                modified = True

        if modified:
            # Canonicalise unit field after conversion
            for field in _UNIT_FIELDS:
                if field in payload:
                    payload[field] = "mg/dL"

            # Patch the request body in-place
            normalised = json.dumps(payload).encode("utf-8")
            request._body = normalised  # type: ignore[attr-defined]

        return request
