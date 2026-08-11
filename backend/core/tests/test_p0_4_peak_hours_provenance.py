from dataclasses import asdict

from companion.deep_memory import IAminaDeepMemory
from companion.memory_truth import (
    SNAPSHOT_SCHEMA,
    SNAPSHOT_VERSION,
    decode_snapshot,
    encode_snapshot,
    snapshot_field_truth,
)
from core.contracts.truth import TruthKind, TruthRecord


def _defaults(patient_id: int) -> dict:
    return asdict(IAminaDeepMemory(patient_id=patient_id))


def test_legacy_peak_hours_is_heuristic_not_clinical_derivation():
    kind, source = snapshot_field_truth("deep", "peak_hours")

    assert kind is TruthKind.HEURISTIC_INFERENCE
    assert source == "legacy.peak_hours"

    record = TruthRecord(
        key="peak_hours",
        value=[8, 20],
        kind=kind,
        source=source,
    )
    assert record.may_persist_as_patient_fact is False
    assert record.may_enter_deterministic_clinical_logic is False


def test_p0_4_v2_peak_hours_marker_migrates_without_reauthorizing():
    payload = {
        "schema": SNAPSHOT_SCHEMA,
        "schema_version": 2,
        "kind": "deep",
        "values": {
            "patient_id": 31,
            "peak_hours": [8, 20],
        },
        "provenance": {
            "peak_hours": {
                "kind": TruthKind.DETERMINISTIC_DERIVATION.value,
                "source": "legacy.peak_hours",
            }
        },
    }

    decoded = decode_snapshot("deep", payload, defaults=_defaults(31))
    assert decoded["peak_hours"] == [8, 20]

    reencoded = encode_snapshot("deep", decoded)
    assert reencoded["schema_version"] == SNAPSHOT_VERSION
    assert reencoded["provenance"]["peak_hours"] == {
        "kind": TruthKind.HEURISTIC_INFERENCE.value,
        "source": "legacy.peak_hours",
    }
