"""Canonical truth classification and legacy snapshot normalization for IAmina memory.

Snapshot JSON is data, not authority. Truth classification lives in code and is
never trusted from persisted metadata.
"""
from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import Any

from core.contracts.truth import TruthKind

SNAPSHOT_VERSION = 1

_MEMORY_TRUTH = MappingProxyType(
    {
        "patterns": TruthKind.CONVERSATIONAL_STATE,
        "last_concern": TruthKind.USER_CLAIM,
        "current_tone": TruthKind.CONVERSATIONAL_STATE,
        "emotional_signals": TruthKind.CONVERSATIONAL_STATE,
        "milestones_celebrated": TruthKind.CONVERSATIONAL_STATE,
        "cached_stats": TruthKind.CONVERSATIONAL_STATE,
        "legacy_unknown_fields": TruthKind.CONVERSATIONAL_STATE,
    }
)

_DEEP_TRUTH = MappingProxyType(
    {
        "significant_events": TruthKind.CONVERSATIONAL_STATE,
        "food_sensitivities": TruthKind.MODEL_INFERENCE,
        "quarantined_heuristics": TruthKind.MODEL_INFERENCE,
        "peak_hours": TruthKind.CONVERSATIONAL_STATE,
        "relationship_stage": TruthKind.CONVERSATIONAL_STATE,
        "communication_style": TruthKind.CONVERSATIONAL_STATE,
        "total_interactions": TruthKind.CONVERSATIONAL_STATE,
        "last_log_date": TruthKind.CONVERSATIONAL_STATE,
        "consecutive_log_days": TruthKind.CONVERSATIONAL_STATE,
        "longest_streak": TruthKind.CONVERSATIONAL_STATE,
        "last_advice_given_at": TruthKind.CONVERSATIONAL_STATE,
        "legacy_unknown_fields": TruthKind.CONVERSATIONAL_STATE,
    }
)

_MEMORY_KEYS = frozenset({"patient_id", "snapshot_version", *_MEMORY_TRUTH.keys()})
_DEEP_KEYS = frozenset({"patient_id", "snapshot_version", *_DEEP_TRUTH.keys()})
_UNTRUSTED_METADATA_KEYS = frozenset({"truth_kinds", "truth_provenance"})


def truth_kind_for(snapshot_kind: str, field_name: str) -> TruthKind:
    """Return the canonical provenance class for a memory field."""

    table = {"memory": _MEMORY_TRUTH, "deep": _DEEP_TRUTH}.get(snapshot_kind)
    if table is None:
        raise ValueError(f"unknown snapshot kind: {snapshot_kind!r}")
    try:
        return table[field_name]
    except KeyError:
        raise KeyError(f"unclassified {snapshot_kind} field: {field_name!r}") from None


def _legacy_unknown_fields(raw: dict[str, Any], known: frozenset[str]) -> dict[str, Any]:
    preserved = raw.get("legacy_unknown_fields")
    unknown = deepcopy(preserved) if isinstance(preserved, dict) else {}
    for key, value in raw.items():
        if key not in known and key not in _UNTRUSTED_METADATA_KEYS:
            unknown.setdefault(key, deepcopy(value))
    return unknown


def normalize_memory_snapshot(data: dict | None, patient_id: int) -> dict[str, Any]:
    """Upgrade an unversioned/legacy memory snapshot to the canonical v1 shape."""

    raw = dict(data or {})
    return {
        "patient_id": patient_id,
        "patterns": list(raw.get("patterns") or []),
        "last_concern": raw.get("last_concern"),
        "current_tone": raw.get("current_tone") or "encouraging",
        "emotional_signals": list(raw.get("emotional_signals") or []),
        "milestones_celebrated": list(raw.get("milestones_celebrated") or []),
        "cached_stats": dict(raw.get("cached_stats") or {}),
        "snapshot_version": SNAPSHOT_VERSION,
        "legacy_unknown_fields": _legacy_unknown_fields(raw, _MEMORY_KEYS),
    }


def normalize_deep_snapshot(data: dict | None, patient_id: int) -> dict[str, Any]:
    """Upgrade a deep-memory snapshot and quarantine the legacy meal heuristic.

    `food_sensitivities` was historically learned from a single post-meal reading
    and an approximate baseline. It is retained only for audit/backward
    compatibility and is not restored into active reasoning state.
    """

    raw = dict(data or {})
    quarantine = raw.get("quarantined_heuristics")
    quarantine = deepcopy(quarantine) if isinstance(quarantine, dict) else {}

    legacy_food = raw.get("food_sensitivities")
    if isinstance(legacy_food, dict) and legacy_food:
        quarantine.setdefault("food_sensitivities", deepcopy(legacy_food))

    return {
        "patient_id": patient_id,
        "significant_events": list(raw.get("significant_events") or []),
        "food_sensitivities": {},
        "quarantined_heuristics": quarantine,
        "peak_hours": list(raw.get("peak_hours") or []),
        "relationship_stage": raw.get("relationship_stage") or "new",
        "communication_style": raw.get("communication_style") or "unknown",
        "total_interactions": int(raw.get("total_interactions") or 0),
        "last_log_date": raw.get("last_log_date"),
        "consecutive_log_days": int(raw.get("consecutive_log_days") or 0),
        "longest_streak": int(raw.get("longest_streak") or 0),
        "last_advice_given_at": raw.get("last_advice_given_at"),
        "snapshot_version": SNAPSHOT_VERSION,
        "legacy_unknown_fields": _legacy_unknown_fields(raw, _DEEP_KEYS),
    }
