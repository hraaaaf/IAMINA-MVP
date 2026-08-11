import json
from types import SimpleNamespace

from companion.deep_memory import IAminaDeepMemory
from companion.memory import IAminaMemory
from companion.memory_truth import (
    SNAPSHOT_VERSION,
    normalize_deep_snapshot,
    normalize_memory_snapshot,
    truth_kind_for,
)
from companion.state import compute_state
from core.contracts.truth import TruthKind, TruthRecord


def test_memory_truth_classification_is_code_owned_and_non_clinical_by_default():
    assert truth_kind_for("memory", "last_concern") is TruthKind.USER_CLAIM
    assert truth_kind_for("memory", "cached_stats") is TruthKind.CONVERSATIONAL_STATE
    assert truth_kind_for("deep", "food_sensitivities") is TruthKind.HEURISTIC_INFERENCE
    assert truth_kind_for("deep", "relationship_stage") is TruthKind.CONVERSATIONAL_STATE

    heuristic = TruthRecord(
        key="food_sensitivities",
        value={"pizza": 70.0},
        kind=truth_kind_for("deep", "food_sensitivities"),
        source="companion.deep_memory.legacy",
    )
    assert heuristic.may_enter_deterministic_clinical_logic is False
    assert heuristic.may_persist_as_patient_fact is False


def test_legacy_memory_snapshot_is_upgraded_without_trusting_snapshot_metadata():
    legacy = {
        "patient_id": 999,
        "patterns": ["OLD_PATTERN"],
        "last_concern": "Je suis inquiet",
        "current_tone": "gentle",
        "emotional_signals": ["anxiety"],
        "milestones_celebrated": ["first_10_logs"],
        "cached_stats": {"last_glucose": 123.0, "log_count": 10},
        "truth_kinds": {"cached_stats": "observed_fact"},
        "legacy_extra": {"keep": True},
    }

    normalized = normalize_memory_snapshot(legacy, patient_id=42)

    assert normalized["patient_id"] == 42
    assert normalized["snapshot_version"] == SNAPSHOT_VERSION
    assert normalized["cached_stats"] == legacy["cached_stats"]
    assert normalized["last_concern"] == legacy["last_concern"]
    assert normalized["legacy_unknown_fields"] == {"legacy_extra": {"keep": True}}
    assert "truth_kinds" not in normalized


def test_memory_load_normalizes_unversioned_cache(monkeypatch):
    legacy = {
        "patient_id": 7,
        "last_concern": "ancienne préoccupation",
        "cached_stats": {"last_glucose": 111.0, "log_count": 3},
    }
    monkeypatch.setattr(
        "companion.memory.cache.get",
        lambda _key: json.dumps(legacy),
    )

    memory = IAminaMemory.load(SimpleNamespace(id=7))

    assert memory.snapshot_version == SNAPSHOT_VERSION
    assert memory.last_concern == "ancienne préoccupation"
    assert memory.cached_stats["last_glucose"] == 111.0


def test_legacy_food_heuristic_is_preserved_only_in_quarantine():
    legacy = {
        "patient_id": 5,
        "food_sensitivities": {"pizza": 72.5},
        "relationship_stage": "building",
        "total_interactions": 12,
        "unknown_old_field": "preserve-me",
    }

    normalized = normalize_deep_snapshot(legacy, patient_id=5)

    assert normalized["snapshot_version"] == SNAPSHOT_VERSION
    assert normalized["food_sensitivities"] == {}
    assert normalized["quarantined_heuristics"]["food_sensitivities"] == {"pizza": 72.5}
    assert normalized["relationship_stage"] == "building"
    assert normalized["total_interactions"] == 12
    assert normalized["legacy_unknown_fields"]["unknown_old_field"] == "preserve-me"


def test_deep_snapshot_tolerates_malformed_legacy_counters():
    normalized = normalize_deep_snapshot(
        {
            "total_interactions": "not-a-number",
            "consecutive_log_days": None,
            "longest_streak": "5",
        },
        patient_id=9,
    )

    assert normalized["total_interactions"] == 0
    assert normalized["consecutive_log_days"] == 0
    assert normalized["longest_streak"] == 5


def test_deep_memory_load_quarantines_unversioned_food_heuristic(monkeypatch):
    legacy = {
        "patient_id": 8,
        "food_sensitivities": {"msemen": 65.0},
        "consecutive_log_days": 4,
    }
    monkeypatch.setattr(
        "companion.deep_memory.cache.get",
        lambda _key: json.dumps(legacy),
    )

    deep = IAminaDeepMemory.load(SimpleNamespace(id=8))

    assert deep.food_sensitivities == {}
    assert deep.quarantined_heuristics["food_sensitivities"] == {"msemen": 65.0}
    assert deep.consecutive_log_days == 4


def test_legacy_learning_api_can_only_write_quarantine():
    deep = IAminaDeepMemory(patient_id=1)

    deep.learn_food_sensitivity("Pizza", 70.0)

    assert deep.food_sensitivities == {}
    assert deep.quarantined_heuristics["food_sensitivities"]["pizza"] == 70.0


def test_quarantined_or_manually_injected_food_heuristic_cannot_steer_next_intention():
    memory = IAminaMemory(patient_id=1)
    deep = IAminaDeepMemory(
        patient_id=1,
        food_sensitivities={"pizza": 70.0},
        quarantined_heuristics={"food_sensitivities": {"pizza": 70.0}},
    )
    ctx = SimpleNamespace(
        tone_signals={},
        trend={},
        primary_label="TIR",
    )

    state = compute_state(memory, deep, ctx)

    assert state.next_intention == "écouter et accompagner"
