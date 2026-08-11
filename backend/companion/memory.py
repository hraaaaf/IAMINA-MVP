import json
import logging
from dataclasses import dataclass, field, fields
from typing import Optional

from django.core.cache import cache

from companion.memory_truth import decode_snapshot, encode_snapshot

logger = logging.getLogger(__name__)


@dataclass
class IAminaMemory:
    patient_id: int
    patterns: list[str] = field(default_factory=list)
    last_concern: Optional[str] = None
    current_tone: str = "encouraging"
    emotional_signals: list[str] = field(default_factory=list)
    milestones_celebrated: list[str] = field(default_factory=list)
    cached_stats: dict = field(default_factory=dict)

    # These copies are runtime-only provenance guards.  Old code may still
    # assign model output directly to the public fields; save() persists only
    # the conversation state accepted by deterministic keyword handling.
    _trusted_last_concern: Optional[str] = field(
        default=None, init=False, repr=False, compare=False
    )
    _trusted_current_tone: str = field(
        default="encouraging", init=False, repr=False, compare=False
    )
    _trusted_emotional_signals: list[str] = field(
        default_factory=list, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        self._trusted_last_concern = self.last_concern
        self._trusted_current_tone = self.current_tone
        self._trusted_emotional_signals = list(self.emotional_signals)

    def _public_values(self) -> dict:
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if not f.name.startswith("_")
        }

    def _snapshot_values(self) -> dict:
        """Return only provenance-approved values for durable persistence."""
        values = self._public_values()
        values["last_concern"] = self._trusted_last_concern
        values["current_tone"] = self._trusted_current_tone
        values["emotional_signals"] = list(self._trusted_emotional_signals)
        return values

    def _restore_trusted_conversation_state(self) -> None:
        """Remove any unapproved/model mutation from the live object after save."""
        self.last_concern = self._trusted_last_concern
        self.current_tone = self._trusted_current_tone
        self.emotional_signals = list(self._trusted_emotional_signals)

    def _record_keyword_emotion(self, signal: str, concern: str) -> None:
        """Accept deterministic keyword-derived conversational state."""
        if signal not in self._trusted_emotional_signals:
            self._trusted_emotional_signals.append(signal)
        self._trusted_last_concern = concern[:100]
        self._trusted_current_tone = "gentle"
        self._restore_trusted_conversation_state()

    @classmethod
    def load(cls, patient) -> "IAminaMemory":
        defaults = cls(patient_id=patient.id)._public_values()

        # 1. Hot path: in-process / Redis cache
        raw = cache.get(f"iamina:memory:{patient.id}")
        if raw:
            try:
                payload = json.loads(raw) if isinstance(raw, str) else raw
                data = decode_snapshot("memory", payload, defaults=defaults)
                return cls(**data)
            except Exception:
                pass

        # 2. Cold path: durable snapshot via the registered store (server restart /
        #    Redis eviction). The active module supplies the SnapshotStore adapter.
        try:
            from core.companion.ports import get_snapshot_store
            store = get_snapshot_store()
            if store is not None:
                payload = store.load("memory", patient.id)
                if payload:
                    data = decode_snapshot("memory", payload, defaults=defaults)
                    obj = cls(**data)
                    # Warm cache in the new explicit v2 envelope even when the DB
                    # row was a legacy flat snapshot.  The DB upgrades on next save.
                    cache.set(
                        f"iamina:memory:{patient.id}",
                        json.dumps(encode_snapshot("memory", obj._snapshot_values())),
                        timeout=60 * 60 * 24 * 90,
                    )
                    return obj
        except Exception:
            logger.exception("IAminaMemory.load snapshot fallback failed for patient=%s", patient.id)

        return cls(patient_id=patient.id)

    def save(self):
        values = self._snapshot_values()
        envelope = encode_snapshot("memory", values)
        payload = json.dumps(envelope)

        # Model output is never allowed to remain in the live memory after a
        # persistence boundary, even if an older caller assigned it directly.
        self._restore_trusted_conversation_state()

        # 1. Cache (fast, 90-day TTL)
        cache.set(f"iamina:memory:{self.patient_id}", payload, timeout=60 * 60 * 24 * 90)

        # 2. Durable snapshot via the registered store (survives restarts)
        try:
            from core.companion.ports import get_snapshot_store
            store = get_snapshot_store()
            if store is not None:
                store.save("memory", self.patient_id, envelope)
        except Exception:
            logger.exception("IAminaMemory.save snapshot failed for patient=%s", self.patient_id)

    def update(self, entry):
        glucose = getattr(entry, "blood_sugar", None)
        if glucose is not None:
            self.cached_stats["last_glucose"] = float(glucose)
            self.cached_stats["last_meal"] = getattr(entry, "meal_type", None) or ""
            self.cached_stats["log_count"] = self.cached_stats.get("log_count", 0) + 1
            _check_milestones(self)
        self.save()

    def update_from_chat(self, message: str, response: str):
        _detect_emotional_signals(message, self)
        self.save()


def _detect_emotional_signals(message: str, memory: IAminaMemory):
    """
    Keyword-based distress detection (FR + Darija transliteration + English).
    Synced with conversation._EMOTIONAL_RE — both must cover the same vocabulary.
    Overrides current_tone to 'gentle' on distress detection.
    """
    signals = {
        # French
        "j'en ai marre": "discouragement",
        "jen ai marre": "discouragement",
        "j'en peux plus": "discouragement",
        "ras le bol": "discouragement",
        "ras-le-bol": "discouragement",
        "découragé": "discouragement",
        "découragée": "discouragement",
        "c'est trop": "discouragement",
        "j'abandonne": "discouragement",
        "fatigué": "fatigue",
        "fatiguée": "fatigue",
        "épuisé": "fatigue",
        "épuisée": "fatigue",
        "à quoi ça sert": "discouragement",
        "peur": "fear",
        "inquiet": "anxiety",
        "inquiète": "anxiety",
        # Darija (Latin transliteration — synced with _EMOTIONAL_RE)
        "3yayt": "fatigue",
        "3yit": "fatigue",
        "t3bna": "fatigue",
        "t3bit": "fatigue",
        "ma b9ich": "discouragement",
        "mab9inch": "discouragement",
        "ma nqderch": "discouragement",
        "ma nqdarch": "discouragement",
        "khlass": "discouragement",
        "bghit nwaqaf": "discouragement",
        "nstah": "discouragement",
        "khayef": "fear",
        "khayfa": "fear",
        "mherres": "discouragement",
        # English
        "i give up": "discouragement",
        "i'm done": "discouragement",
        "can't do this": "discouragement",
        "so tired": "fatigue",
        "exhausted": "fatigue",
        "hopeless": "discouragement",
    }

    msg_lower = message.lower()
    for keyword, signal in signals.items():
        if keyword in msg_lower and signal not in memory.emotional_signals:
            memory._record_keyword_emotion(signal, message)


def _check_milestones(memory: IAminaMemory) -> None:
    """Detect simple streak/count milestones from cached_stats (no SQL cost)."""
    count = memory.cached_stats.get("log_count", 0)
    thresholds = {
        10:  "first_10_logs",
        50:  "logs_50",
        100: "logs_100",
    }
    for threshold, key in thresholds.items():
        if count >= threshold and key not in memory.milestones_celebrated:
            memory.milestones_celebrated.append(key)
