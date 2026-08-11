from dataclasses import asdict

from companion.deep_memory import IAminaDeepMemory
from companion.memory_truth import decode_snapshot, encode_snapshot, snapshot_field_truth
from core.contracts.truth import TruthKind, TruthRecord


def _deep_defaults(patient_id: int = 1) -> dict:
    return asdict(IAminaDeepMemory(patient_id=patient_id))


def test_legacy_food_response_is_heuristic_not_clinical_derivation():
    kind, source = snapshot_field_truth("deep", "food_sensitivities")

    assert kind is TruthKind.HEURISTIC_INFERENCE
    assert source == "legacy.food_response_heuristic"

    record = TruthRecord(
        key="food_sensitivities",
        value={"couscous": 42.5},
        kind=kind,
        source=source,
    )
    assert record.may_persist_as_patient_fact is False
    assert record.may_enter_deterministic_clinical_logic is False


def test_legacy_peak_hours_are_heuristic_not_clinical_derivation():
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


def test_new_v2_encode_writes_corrected_heuristic_provenance():
    values = _deep_defaults(7)
    values["food_sensitivities"] = {"pizza": 30.0}
    values["peak_hours"] = [13]

    payload = encode_snapshot("deep", values)

    assert payload["provenance"]["food_sensitivities"] == {
        "kind": TruthKind.HEURISTIC_INFERENCE.value,
        "source": "legacy.food_response_heuristic",
    }
    assert payload["provenance"]["peak_hours"] == {
        "kind": TruthKind.HEURISTIC_INFERENCE.value,
        "source": "legacy.peak_hours",
    }


def test_pr114_v2_markers_remain_backward_compatible_without_reauthorizing_them():
    values = _deep_defaults(8)
    values["food_sensitivities"] = {"msemen": 65.0}
    values["peak_hours"] = [9, 21]
    payload = encode_snapshot("deep", values)

    # Exact marker emitted briefly by PR #114 before the provenance correction.
    payload["provenance"]["food_sensitivities"] = {
        "kind": TruthKind.DETERMINISTIC_DERIVATION.value,
        "source": "legacy.food_response_heuristic",
    }
    payload["provenance"]["peak_hours"] = {
        "kind": TruthKind.DETERMINISTIC_DERIVATION.value,
        "source": "legacy.peak_hours",
    }

    decoded = decode_snapshot("deep", payload, defaults=_deep_defaults(8))

    assert decoded["food_sensitivities"] == {"msemen": 65.0}
    assert decoded["peak_hours"] == [9, 21]

    reencoded = encode_snapshot("deep", decoded)
    assert reencoded["provenance"]["food_sensitivities"]["kind"] == (
        TruthKind.HEURISTIC_INFERENCE.value
    )
    assert reencoded["provenance"]["peak_hours"]["kind"] == (
        TruthKind.HEURISTIC_INFERENCE.value
    )


def test_arbitrary_wrong_heuristic_marker_still_fails_closed():
    values = _deep_defaults(9)
    values["food_sensitivities"] = {"pizza": 80.0}
    payload = encode_snapshot("deep", values)
    payload["provenance"]["food_sensitivities"] = {
        "kind": TruthKind.MODEL_INFERENCE.value,
        "source": "model",
    }

    decoded = decode_snapshot("deep", payload, defaults=_deep_defaults(9))

    assert decoded["food_sensitivities"] == {}
