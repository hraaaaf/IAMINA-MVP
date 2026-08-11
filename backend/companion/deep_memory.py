import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Optional

from django.core.cache import cache

from companion.memory_truth import decode_snapshot, encode_snapshot
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
    food_sensitivities: dict = field(default_factory=dict)
    peak_hours: list = field(default_factory=list)
    relationship_stage: str = "new"
    communication_style: str = "unknown"
    total_interactions: int = 0
    last_log_date: Optional[str] = None
    consecutive_log_days: int = 0
    longest_streak: int = 0
    last_advice_given_at: Optional[str] = None

    @classmethod
    def load(cls, patient) -> "IAminaDeepMemory":
        key = f"iamina:deep:{patient.id}"
        defaults = asdict(cls(patient_id=patient.id))
        raw = cache.get(key)
        if raw:
            try:
                payload = json.loads(raw) if isinstance(raw, str) else raw
                data = decode_snapshot("deep", payload, defaults=defaults)
                return cls(**data)
            except Exception:
                pass

        try:
            from core.companion.ports import get_snapshot_store
            store = get_snapshot_store()
            if store is not None:
                payload = store.load("deep", patient.id)
                if payload:
                    data = decode_snapshot("deep", payload, defaults=defaults)
                    obj = cls(**data)
                    cache.set(
                        key,
                        json.dumps(encode_snapshot("deep", asdict(obj))),
                        timeout=_TTL,
                    )
                    return obj
        except Exception:
            logger.exception("IAminaDeepMemory.load snapshot fallback failed for patient=%s", patient.id)

        return cls(patient_id=patient.id)

    def save(self):
        key = f"iamina:deep:{self.patient_id}"
        envelope = encode_snapshot("deep", asdict(self))
        payload = json.dumps(envelope)
        cache.set(key, payload, timeout=_TTL)

        try:
            from core.companion.ports import get_snapshot_store
            store = get_snapshot_store()
            if store is not None:
                store.save("deep", self.patient_id, envelope)
        except Exception:
            logger.exception("IAminaDeepMemory.save snapshot failed for patient=%s", self.patient_id)

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
        """Legacy deterministic heuristic retained for snapshot compatibility.

        P0.4 removes the active orchestrator call and patient-facing prompt use.
        The method stays temporarily so old code/tests can decode historical
        snapshots without a breaking API deletion inside this focused lot.
        """
        alpha = 0.3
        name = food_name.lower().strip()
        if name in self.food_sensitivities:
            self.food_sensitivities[name] = round(
                alpha * delta_glucose + (1 - alpha) * self.food_sensitivities[name], 4
            )
        else:
            self.food_sensitivities[name] = round(delta_glucose, 4)

    def update_streak(self, today_has_log: bool):
        today = date.today().isoformat()
        if not today_has_log:
            _streak_before = self.consecutive_log_days
            self.consecutive_log_days = 0
            track(EVT_STREAK_BROKEN, patient_id=self.patient_id, props={"streak_before": _streak_before})
            return

        if self.last_log_date == today:
            return

        (date.today().replace(day=date.today().day - 1) if date.today().day > 1
                     else None)
        # Use date arithmetic properly
        from datetime import timedelta
        yesterday_iso = (date.today() - timedelta(days=1)).isoformat()

        if self.last_log_date == yesterday_iso:
            self.consecutive_log_days += 1
            track(EVT_STREAK_CONTINUED, patient_id=self.patient_id, props={"streak": self.consecutive_log_days})
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
