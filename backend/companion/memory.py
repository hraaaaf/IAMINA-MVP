import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Optional

from django.core.cache import cache

from companion.memory_truth import SNAPSHOT_VERSION, normalize_memory_snapshot, truth_kind_for
from core.contracts.truth import TruthKind

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
    snapshot_version: int = SNAPSHOT_VERSION
    legacy_unknown_fields: dict = field(default_factory=dict)

    @classmethod
    def load(cls, patient) -> "IAminaMemory":
        # 1. Hot path: in-process / Redis cache
        raw = cache.get(f"iamina:memory:{patient.id}")
        if raw:
            try:
                data = normalize_memory_snapshot(json.loads(raw), patient.id)
                return cls(**data)
            except Exception:
                logger.exception("IAminaMemory.load cache normalization failed for patient=%s", patient.id)

        # 2. Cold path: durable snapshot via the registered store (server restart /
        #    Redis eviction). The active module supplies the SnapshotStore adapter.
        try:
            from core.companion.ports import get_snapshot_store

            store = get_snapshot_store()
            if store is not None:
                data = store.load("memory", patient.id)
                if data:
                    normalized = normalize_memory_snapshot(data, patient.id)
                    obj = cls(**normalized)
                    # Warm the cache with the canonical versioned shape.
                    cache.set(
                        f"iamina:memory:{patient.id}",
                        json.dumps(normalized),
                        timeout=60 * 60 * 24 * 90,
                    )
                    return obj
        except Exception:
            logger.exception("IAminaMemory.load snapshot fallback failed for patient=%s", patient.id)

        return cls(patient_id=patient.id)

    def save(self):
        normalized = normalize_memory_snapshot(asdict(self), self.patient_id)
        payload = json.dumps(normalized)

        # 1. Cache (fast, 90-day TTL)
        cache.set(f"iamina:memory:{self.patient_id}", payload, timeout=60 * 60 * 24 * 90)

        # 2. Durable snapshot via the registered store (survives restarts)
        try:
            from core.companion.ports import get_snapshot_store

            store = get_snapshot_store()
            if store is not None:
                store.save("memory", self.patient_id, normalized)
        except Exception:
            logger.exception("IAminaMemory.save snapshot failed for patient=%s", self.patient_id)

    def truth_kind_for(self, field_name: str) -> TruthKind:
        """Return the canonical, code-owned truth class for a memory field."""

        return truth_kind_for("memory", field_name)

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
    distress = {"discouragement", "fatigue", "fear", "anxiety"}
    detected_distress = False

    msg_lower = message.lower()
    for keyword, signal in signals.items():
        if keyword in msg_lower and signal not in memory.emotional_signals:
            memory.emotional_signals.append(signal)
            memory.last_concern = message[:100]
            if signal in distress:
                detected_distress = True

    if detected_distress and memory.current_tone != "gentle":
        memory.current_tone = "gentle"


def _check_milestones(memory: IAminaMemory) -> None:
    """Detect simple streak/count milestones from cached_stats (no SQL cost)."""
    count = memory.cached_stats.get("log_count", 0)
    thresholds = {
        10: "first_10_logs",
        50: "logs_50",
        100: "logs_100",
    }
    for threshold, key in thresholds.items():
        if count >= threshold and key not in memory.milestones_celebrated:
            memory.milestones_celebrated.append(key)
