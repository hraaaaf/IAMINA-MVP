import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Optional

from django.core.cache import cache

from companion.memory_truth import SNAPSHOT_VERSION, normalize_deep_snapshot, truth_kind_for
from core.contracts.truth import TruthKind
from core.observability import EVT_STREAK_BROKEN, EVT_STREAK_CONTINUED, track

logger = logging.getLogger(__name__)

_TTL = 60 * 60 * 24 * 90  # 90 days

_RELATIONSHIP_THRESHOLDS = {
    "new": 5,
    "building": 20,
    "trusted": 50,
}


@dataclass
class IAminaDeepMemory:
    patient_id: int
    significant_events: list = field(default_factory=list)
    # Compatibility-only field. Canonical loading keeps it empty and moves old
    # values to quarantined_heuristics so they cannot steer active reasoning.
    food_sensitivities: dict = field(default_factory=dict)
    quarantined_heuristics: dict = field(default_factory=dict)
    peak_hours: list = field(default_factory=list)
    relationship_stage: str = "new"
    communication_style: str = "unknown"
    total_interactions: int = 0
    last_log_date: Optional[str] = None
    consecutive_log_days: int = 0
    longest_streak: int = 0
    last_advice_given_at: Optional[str] = None
    snapshot_version: int = SNAPSHOT_VERSION
    legacy_unknown_fields: dict = field(default_factory=dict)

    @classmethod
    def load(cls, patient) -> "IAminaDeepMemory":
        key = f"iamina:deep:{patient.id}"
        raw = cache.get(key)
        if raw:
            try:
                data = normalize_deep_snapshot(json.loads(raw), patient.id)
                return cls(**data)
            except Exception:
                logger.exception(
                    "IAminaDeepMemory.load cache normalization failed for patient=%s",
                    patient.id,
                )

        try:
            from core.companion.ports import get_snapshot_store

            store = get_snapshot_store()
            if store is not None:
                data = store.load("deep", patient.id)
                if data:
                    normalized = normalize_deep_snapshot(data, patient.id)
                    obj = cls(**normalized)
                    cache.set(key, json.dumps(normalized), timeout=_TTL)
                    return obj
        except Exception:
            logger.exception("IAminaDeepMemory.load snapshot fallback failed for patient=%s", patient.id)

        return cls(patient_id=patient.id)

    def save(self):
        normalized = normalize_deep_snapshot(asdict(self), self.patient_id)
        # Keep the in-memory object aligned with the durable canonical shape.
        self.food_sensitivities = {}
        self.quarantined_heuristics = normalized["quarantined_heuristics"]
        self.snapshot_version = SNAPSHOT_VERSION
        self.legacy_unknown_fields = normalized["legacy_unknown_fields"]

        key = f"iamina:deep:{self.patient_id}"
        payload = json.dumps(normalized)
        cache.set(key, payload, timeout=_TTL)

        try:
            from core.companion.ports import get_snapshot_store

            store = get_snapshot_store()
            if store is not None:
                store.save("deep", self.patient_id, normalized)
        except Exception:
            logger.exception("IAminaDeepMemory.save snapshot failed for patient=%s", self.patient_id)

    def truth_kind_for(self, field_name: str) -> TruthKind:
        """Return the canonical, code-owned truth class for a deep-memory field."""

        return truth_kind_for("deep", field_name)

    def record_event(self, type: str, description: str, glucose: Optional[float] = None):
        from datetime import datetime, timezone

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": type,
            "description": description,
        }
        if glucose is not None:
            event["glucose"] = glucose
        self.significant_events.append(event)
        if len(self.significant_events) > 20:
            self.significant_events = self.significant_events[-20:]

    def learn_food_sensitivity(self, food_name: str, delta_glucose: float):
        """Retain legacy API compatibility while quarantining heuristic output.

        This method no longer creates active patient knowledge. Existing callers
        cannot make the heuristic influence IAmina's clinical or dialogue state.
        """

        alpha = 0.3
        name = food_name.lower().strip()
        bucket = self.quarantined_heuristics.setdefault("food_sensitivities", {})
        if name in bucket:
            bucket[name] = round(alpha * delta_glucose + (1 - alpha) * bucket[name], 4)
        else:
            bucket[name] = round(delta_glucose, 4)
        self.food_sensitivities = {}

    def update_streak(self, today_has_log: bool):
        today = date.today().isoformat()
        if not today_has_log:
            _streak_before = self.consecutive_log_days
            self.consecutive_log_days = 0
            track(
                EVT_STREAK_BROKEN,
                patient_id=self.patient_id,
                props={"streak_before": _streak_before},
            )
            return

        if self.last_log_date == today:
            return

        # Use date arithmetic properly
        from datetime import timedelta

        yesterday_iso = (date.today() - timedelta(days=1)).isoformat()

        if self.last_log_date == yesterday_iso:
            self.consecutive_log_days += 1
            track(
                EVT_STREAK_CONTINUED,
                patient_id=self.patient_id,
                props={"streak": self.consecutive_log_days},
            )
        else:
            self.consecutive_log_days = 1

        self.last_log_date = today
        if self.consecutive_log_days > self.longest_streak:
            self.longest_streak = self.consecutive_log_days

    def evolve_relationship(self, emotional_signals: Optional[list] = None):
        stages = ["new", "building", "trusted", "companion"]
        current_idx = stages.index(self.relationship_stage) if self.relationship_stage in stages else 0

        if current_idx >= len(stages) - 1:
            return

        next_stage = stages[current_idx + 1]
        threshold = _RELATIONSHIP_THRESHOLDS.get(self.relationship_stage)

        if threshold is None:
            return

        bonus = len(emotional_signals) if emotional_signals else 0
        effective_interactions = self.total_interactions + bonus

        if effective_interactions >= threshold:
            self.relationship_stage = next_stage

    def record_advice_given(self) -> None:
        from datetime import datetime, timezone

        self.last_advice_given_at = datetime.now(timezone.utc).isoformat()

    def advice_given_within(self, hours: int = 24) -> bool:
        if not self.last_advice_given_at:
            return False
        from datetime import datetime, timedelta, timezone

        try:
            last = datetime.fromisoformat(self.last_advice_given_at)
            return (datetime.now(timezone.utc) - last) < timedelta(hours=hours)
        except (ValueError, TypeError):
            return False
