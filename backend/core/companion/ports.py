"""
core/companion/ports.py — non-clinical persistence ports for the companion runtime.

The active module registers concrete adapters at startup. If no adapter is
registered (e.g. a minimal test harness), getters return None and callers fall
back to defensive behaviour (empty memory, no persistence).

Scope (P4.5): these ports cover companion *persistence* only — memory snapshots
and conversation history. All *clinical* data (context, narrative, alerts) flows
through the single engine contract instead — see core/companion/clinical.py and
BaseEngine.analyze() → DomainContext.

Ports are narrow and condition-agnostic: they speak patient_id + plain dicts,
never ORM objects or domain vocabulary.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatTurn:
    """A single conversation turn — condition-agnostic (no ORM, no domain data)."""

    role: str       # "user" | "assistant"
    message: str


class SnapshotStore(abc.ABC):
    """
    Durable persistence for companion memory snapshots.

    `kind` namespaces the snapshot ("memory" | "deep"). Implementations map each
    kind to a storage backend (a Django model, a cache, etc.) and round-trip a
    JSON-serializable dict. They must never raise on a missing row — return None.
    """

    @abc.abstractmethod
    def load(self, kind: str, patient_id: int) -> dict | None:
        """Return the stored dict for (kind, patient_id), or None if absent."""

    @abc.abstractmethod
    def save(self, kind: str, patient_id: int, data: dict) -> None:
        """Upsert the dict for (kind, patient_id)."""


class ConversationStore(abc.ABC):
    """
    Durable conversation history for the companion chat loop.

    Speaks in patient_id + ChatTurn; never exposes ORM objects. `recent` returns
    turns newest-first (most recent at index 0), matching the chat loop's
    expectation. `role` optionally filters to one side of the conversation.
    """

    @abc.abstractmethod
    def append(self, patient_id: int, role: str, message: str) -> None:
        """Persist one turn."""

    @abc.abstractmethod
    def recent(
        self, patient_id: int, limit: int, offset: int = 0, role: str | None = None
    ) -> list[ChatTurn]:
        """Return up to `limit` turns, newest-first, skipping `offset` most-recent."""

    @abc.abstractmethod
    def count(self, patient_id: int) -> int:
        """Total number of stored turns for the patient."""


# ── Registry ────────────────────────────────────────────────────────────────
# Module-level singletons set by the active module's AppConfig.ready().

_snapshot_store: SnapshotStore | None = None
_conversation_store: ConversationStore | None = None


def register_snapshot_store(store: SnapshotStore) -> None:
    """Register the active module's SnapshotStore adapter (called in ready())."""
    global _snapshot_store
    _snapshot_store = store


def get_snapshot_store() -> SnapshotStore | None:
    """Resolve the registered SnapshotStore, or None if no module registered one."""
    return _snapshot_store


def register_conversation_store(store: ConversationStore) -> None:
    """Register the active module's ConversationStore adapter (called in ready())."""
    global _conversation_store
    _conversation_store = store


def get_conversation_store() -> ConversationStore | None:
    """Resolve the registered ConversationStore, or None if none registered."""
    return _conversation_store
