"""
diabetes/companion_adapters.py — companion persistence adapters for diabetes.

Registered with the chassis in DiabetesConfig.ready(). Keeps the companion
runtime free of any `diabetes.*` import. Scope is persistence only (memory
snapshots + conversation history); clinical context/narrative/alerts flow
through the engine contract (DiabetesEngine.analyze / evaluate_alert), not here.

Models stay in the `diabetes` app for now; physical relocation to `core` = P7.5.
"""
from __future__ import annotations

import logging

from core.companion.ports import ChatTurn, ConversationStore, SnapshotStore

logger = logging.getLogger(__name__)


class DiabetesSnapshotStore(SnapshotStore):
    """Maps companion snapshot kinds to the diabetes IAmina*Snapshot models."""

    @staticmethod
    def _model(kind: str):
        # Lazy import: models aren't ready at module import time.
        from diabetes.models import IAminaDeepMemorySnapshot, IAminaMemorySnapshot

        models = {
            "memory": IAminaMemorySnapshot,
            "deep": IAminaDeepMemorySnapshot,
        }
        try:
            return models[kind]
        except KeyError:
            raise ValueError(f"Unknown snapshot kind: {kind!r}") from None

    def load(self, kind: str, patient_id: int) -> dict | None:
        snap = self._model(kind).objects.filter(patient_id=patient_id).first()
        if snap and snap.data_json:
            return snap.data_json
        return None

    def save(self, kind: str, patient_id: int, data: dict) -> None:
        self._model(kind).objects.update_or_create(
            patient_id=patient_id,
            defaults={"data_json": data},
        )


class DiabetesConversationStore(ConversationStore):
    """Conversation history backed by the diabetes AIChatMessage model."""

    @staticmethod
    def _model():
        from diabetes.models import AIChatMessage

        return AIChatMessage

    def append(self, patient_id: int, role: str, message: str) -> None:
        self._model().objects.create(patient_id=patient_id, role=role, message=message)

    def recent(
        self, patient_id: int, limit: int, offset: int = 0, role: str | None = None
    ) -> list[ChatTurn]:
        qs = self._model().objects.filter(patient_id=patient_id)
        if role is not None:
            qs = qs.filter(role=role)
        qs = qs.order_by("-created_at")[offset:offset + limit]
        return [ChatTurn(role=m.role, message=m.message) for m in qs]

    def count(self, patient_id: int) -> int:
        return self._model().objects.filter(patient_id=patient_id).count()
