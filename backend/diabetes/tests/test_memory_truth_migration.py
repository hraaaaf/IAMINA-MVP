"""P0.4 regression contracts for IAmina legacy-memory truth migration."""
from __future__ import annotations

import json
from dataclasses import asdict
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from companion.deep_memory import IAminaDeepMemory
from companion.memory import IAminaMemory, _detect_emotional_signals
from companion.memory_truth import (
    SNAPSHOT_SCHEMA,
    SNAPSHOT_VERSION,
    decode_snapshot,
    encode_snapshot,
    snapshot_field_truth,
)
from companion.state import compute_state
from core.contracts.domain_context import DomainContext
from core.contracts.truth import TruthKind


def _memory_defaults(patient_id: int = 1) -> dict:
    return IAminaMemory(patient_id=patient_id)._public_values()


def _deep_defaults(patient_id: int = 1) -> dict:
    return asdict(IAminaDeepMemory(patient_id=patient_id))


def _empty_context() -> DomainContext:
    return DomainContext(
        kpi_summary={},
        detected_patterns=[],
        insights=[],
        pivot_text="",
        language="fr",
        has_sufficient_data=False,
        tone_signals={"primary": None, "stability": None},
        trend={},
        primary_label="TIR",
    )


class SnapshotCodecTest(SimpleTestCase):
    def test_v2_envelope_has_explicit_schema_and_provenance(self):
        values = _memory_defaults(7)
        values["patterns"] = ["overnight_high"]

        payload = encode_snapshot("memory", values)

        self.assertEqual(payload["schema"], SNAPSHOT_SCHEMA)
        self.assertEqual(payload["schema_version"], SNAPSHOT_VERSION)
        self.assertEqual(payload["kind"], "memory")
        self.assertEqual(
            payload["provenance"]["patterns"]["kind"],
            TruthKind.DETERMINISTIC_DERIVATION.value,
        )
        kind, source = snapshot_field_truth("memory", "patterns")
        self.assertEqual(kind, TruthKind.DETERMINISTIC_DERIVATION)
        self.assertEqual(source, "domain_context.detected_patterns")

    def test_v2_round_trip_preserves_known_values(self):
        values = _deep_defaults(8)
        values["relationship_stage"] = "building"
        values["total_interactions"] = 12
        payload = encode_snapshot("deep", values)

        decoded = decode_snapshot("deep", payload, defaults=_deep_defaults(8))

        self.assertEqual(decoded["relationship_stage"], "building")
        self.assertEqual(decoded["total_interactions"], 12)
        self.assertEqual(decoded["patient_id"], 8)

    def test_tampered_provenance_fails_only_field_closed(self):
        values = _memory_defaults(3)
        values["patterns"] = ["overnight_high"]
        payload = encode_snapshot("memory", values)
        payload["provenance"]["patterns"] = {
            "kind": TruthKind.MODEL_INFERENCE.value,
            "source": "model",
        }

        decoded = decode_snapshot("memory", payload, defaults=_memory_defaults(3))

        self.assertEqual(decoded["patterns"], [])
        self.assertEqual(decoded["patient_id"], 3)

    def test_unknown_schema_version_fails_closed(self):
        values = _memory_defaults(4)
        values["patterns"] = ["overnight_high"]
        payload = encode_snapshot("memory", values)
        payload["schema_version"] = 999

        decoded = decode_snapshot("memory", payload, defaults=_memory_defaults(4))

        self.assertEqual(decoded, _memory_defaults(4))

    def test_payload_cannot_override_patient_identity(self):
        values = _deep_defaults(999)
        payload = encode_snapshot("deep", values)

        decoded = decode_snapshot("deep", payload, defaults=_deep_defaults(5))

        self.assertEqual(decoded["patient_id"], 5)

    def test_legacy_memory_keeps_safe_fields_but_quarantines_unproven_emotion(self):
        legacy = _memory_defaults(10)
        legacy.update(
            patterns=["overnight_high"],
            cached_stats={"log_count": 50},
            last_concern="generated concern",
            current_tone="challenge",
            emotional_signals=["generated_signal"],
        )

        decoded = decode_snapshot("memory", legacy, defaults=_memory_defaults(10))

        self.assertEqual(decoded["patterns"], ["overnight_high"])
        self.assertEqual(decoded["cached_stats"], {"log_count": 50})
        self.assertIsNone(decoded["last_concern"])
        self.assertEqual(decoded["current_tone"], "encouraging")
        self.assertEqual(decoded["emotional_signals"], [])

    def test_legacy_deep_food_memory_remains_readable_only_for_compatibility(self):
        legacy = _deep_defaults(11)
        legacy["food_sensitivities"] = {"couscous": 42.5}

        decoded = decode_snapshot("deep", legacy, defaults=_deep_defaults(11))

        self.assertEqual(decoded["food_sensitivities"], {"couscous": 42.5})


class DurableMemoryAuthorityTest(SimpleTestCase):
    @patch("core.companion.ports.get_snapshot_store")
    @patch("companion.memory.cache.set")
    def test_direct_model_like_mutation_is_not_persisted(self, cache_set, get_store):
        store = MagicMock()
        get_store.return_value = store
        memory = IAminaMemory(patient_id=20)

        # Simulates the two historical LLM write paths: concern_detected and
        # tone_detected. Neither was accepted through deterministic provenance.
        memory.last_concern = "model-generated concern"
        memory.current_tone = "challenge"
        memory.emotional_signals.append("model-generated-signal")

        memory.save()

        cached_payload = json.loads(cache_set.call_args.args[1])
        values = cached_payload["values"]
        self.assertIsNone(values["last_concern"])
        self.assertEqual(values["current_tone"], "encouraging")
        self.assertEqual(values["emotional_signals"], [])
        self.assertIsNone(memory.last_concern)
        self.assertEqual(memory.current_tone, "encouraging")
        self.assertEqual(memory.emotional_signals, [])
        store.save.assert_called_once_with("memory", 20, cached_payload)

    @patch("core.companion.ports.get_snapshot_store")
    @patch("companion.memory.cache.set")
    def test_deterministic_keyword_emotion_is_allowed_to_persist(self, cache_set, get_store):
        get_store.return_value = MagicMock()
        memory = IAminaMemory(patient_id=21)

        _detect_emotional_signals("J'en ai marre de tout noter", memory)
        memory.save()

        cached_payload = json.loads(cache_set.call_args.args[1])
        values = cached_payload["values"]
        self.assertEqual(values["last_concern"], "J'en ai marre de tout noter")
        self.assertEqual(values["current_tone"], "gentle")
        self.assertEqual(values["emotional_signals"], ["discouragement"])
        self.assertEqual(
            cached_payload["provenance"]["emotional_signals"],
            {
                "kind": TruthKind.CONVERSATIONAL_STATE.value,
                "source": "companion.keyword_emotion",
            },
        )


class LegacyHeuristicQuarantineTest(SimpleTestCase):
    def test_historical_food_sensitivity_does_not_drive_next_intention(self):
        memory = IAminaMemory(patient_id=30)
        deep = IAminaDeepMemory(
            patient_id=30,
            food_sensitivities={"couscous": 42.5},
        )

        state = compute_state(memory, deep, _empty_context())

        self.assertEqual(state.next_intention, "écouter et accompagner")

    @patch("companion.core.react", return_value="ok")
    @patch("companion.core._evaluate_alert", return_value=None)
    @patch("companion.core._learn_from_entry")
    @patch("companion.core.IAminaDeepMemory.load")
    @patch("companion.core.IAminaMemory.load")
    def test_active_on_log_does_not_feed_legacy_food_heuristic(
        self,
        memory_load,
        deep_load,
        learn_from_entry,
        evaluate_alert,
        react,
    ):
        from companion.core import IAmina

        patient = MagicMock()
        patient.id = 30
        memory = MagicMock(spec=IAminaMemory)
        memory.emotional_signals = []
        deep = MagicMock(spec=IAminaDeepMemory)
        memory_load.return_value = memory
        deep_load.return_value = deep
        entry = MagicMock()
        entry.blood_sugar = 250

        result = IAmina(patient, language="fr").on_log(entry)

        self.assertEqual(result, "ok")
        learn_from_entry.assert_not_called()
        evaluate_alert.assert_called_once()
        react.assert_called_once()
