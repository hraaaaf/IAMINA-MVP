"""Versioned truth/provenance codec for IAmina companion memory snapshots.

P0.4 keeps the existing database models and JSONField storage unchanged. The
payload itself is explicit about schema version, truth kind and stable source so
a durable companion snapshot cannot silently masquerade as clinical patient
truth.

P0.4.1 distinguishes legacy heuristic inference from approved deterministic
clinical derivation. Existing v2 envelopes and older flat snapshots remain
readable, but historical food-response heuristic values are moved into an
explicit quarantine and never restored as active companion knowledge.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.contracts.truth import TruthKind

SNAPSHOT_SCHEMA = "iamina.companion-memory"
SNAPSHOT_VERSION = 3
_LEGACY_ENVELOPE_VERSION = 2

_FIELD_PROVENANCE: dict[str, dict[str, tuple[TruthKind, str]]] = {
    "memory": {
        "patterns": (
            TruthKind.DETERMINISTIC_DERIVATION,
            "domain_context.detected_patterns",
        ),
        "last_concern": (
            TruthKind.CONVERSATIONAL_STATE,
            "companion.keyword_emotion",
        ),
        "current_tone": (
            TruthKind.CONVERSATIONAL_STATE,
            "companion.keyword_emotion",
        ),
        "emotional_signals": (
            TruthKind.CONVERSATIONAL_STATE,
            "companion.keyword_emotion",
        ),
        "milestones_celebrated": (
            TruthKind.DETERMINISTIC_DERIVATION,
            "companion.log_milestones",
        ),
        "cached_stats": (
            TruthKind.DETERMINISTIC_DERIVATION,
            "companion.log_cache",
        ),
    },
    "deep": {
        "significant_events": (
            TruthKind.DETERMINISTIC_DERIVATION,
            "companion.deterministic_events",
        ),
        "food_sensitivities": (
            TruthKind.HEURISTIC_INFERENCE,
            "legacy.food_response_heuristic",
        ),
        "quarantined_heuristics": (
            TruthKind.HEURISTIC_INFERENCE,
            "companion.heuristic_quarantine",
        ),
        "peak_hours": (
            TruthKind.DETERMINISTIC_DERIVATION,
            "legacy.peak_hours",
        ),
        "relationship_stage": (
            TruthKind.CONVERSATIONAL_STATE,
            "companion.relationship_state",
        ),
        "communication_style": (
            TruthKind.CONVERSATIONAL_STATE,
            "companion.communication_state",
        ),
        "total_interactions": (
            TruthKind.CONVERSATIONAL_STATE,
            "companion.interaction_counter",
        ),
        "last_log_date": (
            TruthKind.CONVERSATIONAL_STATE,
            "companion.streak_state",
        ),
        "consecutive_log_days": (
            TruthKind.DETERMINISTIC_DERIVATION,
            "companion.streak_state",
        ),
        "longest_streak": (
            TruthKind.DETERMINISTIC_DERIVATION,
            "companion.streak_state",
        ),
        "last_advice_given_at": (
            TruthKind.CONVERSATIONAL_STATE,
            "companion.advice_throttle",
        ),
    },
}

# Exact provenance emitted by P0.4 v2. It is accepted only to migrate existing
# envelopes safely; new writes always use v3 and the stricter heuristic class.
_V2_FIELD_PROVENANCE: dict[str, dict[str, tuple[TruthKind, str]]] = {
    "memory": _FIELD_PROVENANCE["memory"],
    "deep": {
        field: value
        for field, value in _FIELD_PROVENANCE["deep"].items()
        if field != "quarantined_heuristics"
    }
    | {
        "food_sensitivities": (
            TruthKind.DETERMINISTIC_DERIVATION,
            "legacy.food_response_heuristic",
        )
    },
}

# The old flat snapshot cannot prove whether these fields were created by the
# deterministic keyword detector or by model output. Unknown provenance fails
# closed to neutral conversation state during the one-time legacy read path.
_LEGACY_UNPROVEN_CONVERSATION_FIELDS = frozenset(
    {"last_concern", "current_tone", "emotional_signals"}
)


def _quarantine_deep_food(values: dict[str, Any]) -> dict[str, Any]:
    """Move any legacy/active food heuristic into compatibility-only quarantine."""
    safe = deepcopy(values)
    quarantine = safe.get("quarantined_heuristics")
    quarantine = deepcopy(quarantine) if isinstance(quarantine, dict) else {}
    legacy_food = safe.get("food_sensitivities")
    if isinstance(legacy_food, dict) and legacy_food:
        bucket = quarantine.setdefault("food_sensitivities", {})
        if isinstance(bucket, dict):
            for key, value in legacy_food.items():
                bucket.setdefault(key, deepcopy(value))
    safe["food_sensitivities"] = {}
    safe["quarantined_heuristics"] = quarantine
    return safe


def encode_snapshot(kind: str, values: dict[str, Any]) -> dict[str, Any]:
    """Return a v3 JSON-serializable envelope with explicit field provenance."""
    provenance = _FIELD_PROVENANCE.get(kind)
    if provenance is None:
        raise ValueError(f"Unknown snapshot kind: {kind!r}")

    public_values = deepcopy(values)
    if kind == "deep":
        public_values = _quarantine_deep_food(public_values)

    field_provenance = {
        field: {"kind": truth_kind.value, "source": source}
        for field, (truth_kind, source) in provenance.items()
        if field in public_values
    }
    return {
        "schema": SNAPSHOT_SCHEMA,
        "schema_version": SNAPSHOT_VERSION,
        "kind": kind,
        "values": public_values,
        "provenance": field_provenance,
    }


def decode_snapshot(
    kind: str,
    payload: dict[str, Any] | None,
    *,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    """Decode v3, P0.4 v2 or legacy flat payloads into safe constructor values.

    Unknown schema versions, kind mismatches and malformed envelopes fail closed
    to the supplied defaults. A snapshot can never override the patient_id
    selected by the caller. Deep food-response heuristics are always quarantined.
    """
    current_provenance = _FIELD_PROVENANCE.get(kind)
    if current_provenance is None:
        raise ValueError(f"Unknown snapshot kind: {kind!r}")

    safe_defaults = deepcopy(defaults)
    if not isinstance(payload, dict) or not payload:
        return safe_defaults

    is_envelope = payload.get("schema") == SNAPSHOT_SCHEMA
    if is_envelope:
        version = payload.get("schema_version")
        if version == SNAPSHOT_VERSION:
            provenance = current_provenance
        elif version == _LEGACY_ENVELOPE_VERSION:
            provenance = _V2_FIELD_PROVENANCE[kind]
        else:
            return safe_defaults
        if payload.get("kind") != kind:
            return safe_defaults
        raw_values = payload.get("values")
        raw_provenance = payload.get("provenance")
        if not isinstance(raw_values, dict) or not isinstance(raw_provenance, dict):
            return safe_defaults

        values = deepcopy(raw_values)
        # Provenance metadata is executable. If a field's label or source is
        # missing/tampered, that field alone falls back to neutral.
        for field, (truth_kind, source) in provenance.items():
            if field not in values:
                continue
            marker = raw_provenance.get(field)
            if marker != {"kind": truth_kind.value, "source": source}:
                values[field] = deepcopy(safe_defaults.get(field))
    else:
        # Legacy flat snapshot. Preserve known structures, but do not carry
        # forward conversational fields whose origin cannot be proven.
        values = deepcopy(payload)
        if kind == "memory":
            for field in _LEGACY_UNPROVEN_CONVERSATION_FIELDS:
                if field in safe_defaults:
                    values[field] = deepcopy(safe_defaults[field])

    if kind == "deep":
        values = _quarantine_deep_food(values)

    allowed = set(safe_defaults)
    decoded = {
        key: deepcopy(value)
        for key, value in values.items()
        if key in allowed
    }
    merged = safe_defaults | decoded
    # Caller-selected identity is authoritative; a stale/corrupt payload cannot
    # redirect a snapshot to another patient.
    if "patient_id" in safe_defaults:
        merged["patient_id"] = safe_defaults["patient_id"]
    return merged


def snapshot_field_truth(kind: str, field: str) -> tuple[TruthKind, str]:
    """Expose the canonical provenance label for tests/audits."""
    try:
        return _FIELD_PROVENANCE[kind][field]
    except KeyError:
        raise ValueError(f"Unknown snapshot field: {kind}.{field}") from None
