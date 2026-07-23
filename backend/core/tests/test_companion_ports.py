"""
Companion persistence ports — unit tests (P6.5 → P4.5).

Scope after P4.5: these ports cover companion persistence only (memory snapshots
+ conversation history). Clinical context/narrative/alerts now flow through the
engine contract and are tested in test_base_engine.py.

Covers:
  1. SnapshotStore / ConversationStore are ABCs and register/resolve correctly.
  2. Memory load/save degrade gracefully when no store is registered.
  3. The diabetes adapters round-trip snapshots + chat turns.
  4. Package-wide seam guard: companion/ imports no module package.
"""
import re
from pathlib import Path

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase

from core.companion.ports import (
    ChatTurn,
    ConversationStore,
    SnapshotStore,
    get_conversation_store,
    get_snapshot_store,
    register_conversation_store,
    register_snapshot_store,
)


class _FakeStore(SnapshotStore):
    def __init__(self):
        self.data = {}

    def load(self, kind, patient_id):
        return self.data.get((kind, patient_id))

    def save(self, kind, patient_id, data):
        self.data[(kind, patient_id)] = dict(data)


class SnapshotStorePortTests(SimpleTestCase):
    def test_abc_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            SnapshotStore()

    def test_register_and_get_roundtrip(self):
        original = get_snapshot_store()
        try:
            fake = _FakeStore()
            register_snapshot_store(fake)
            self.assertIs(get_snapshot_store(), fake)
        finally:
            register_snapshot_store(original)


class MemoryWithoutStoreTests(TestCase):
    """With no registered store, memory persistence degrades gracefully."""

    def setUp(self):
        cache.clear()
        self._saved = get_snapshot_store()
        register_snapshot_store(None)  # type: ignore[arg-type]

    def tearDown(self):
        register_snapshot_store(self._saved)
        cache.clear()

    def test_memory_load_save_noop_without_store(self):
        from companion.memory import IAminaMemory

        user = User.objects.create(username="ports_no_store_mem")
        mem = IAminaMemory.load(user)
        mem.patterns.append("x")
        mem.save()  # must not raise even with no store
        cache.clear()
        reloaded = IAminaMemory.load(user)
        self.assertEqual(reloaded.patient_id, user.id)

    def test_deep_load_save_noop_without_store(self):
        from companion.deep_memory import IAminaDeepMemory

        user = User.objects.create(username="ports_no_store_deep")
        deep = IAminaDeepMemory.load(user)
        deep.total_interactions = 3
        deep.save()  # must not raise
        cache.clear()
        reloaded = IAminaDeepMemory.load(user)
        self.assertEqual(reloaded.patient_id, user.id)


class DiabetesSnapshotAdapterTests(TestCase):
    """The diabetes adapter persists snapshots durably across cache eviction."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_adapter_roundtrips_memory(self):
        from companion.memory import IAminaMemory

        user = User.objects.create(username="ports_diab_mem")
        mem = IAminaMemory.load(user)
        mem.patterns.append("dawn_phenomenon")
        mem.save()
        cache.clear()
        reloaded = IAminaMemory.load(user)
        self.assertIn("dawn_phenomenon", reloaded.patterns)

    def test_adapter_roundtrips_deep(self):
        from companion.deep_memory import IAminaDeepMemory

        user = User.objects.create(username="ports_diab_deep")
        deep = IAminaDeepMemory.load(user)
        deep.total_interactions = 7
        deep.relationship_stage = "building"
        deep.save()
        cache.clear()
        reloaded = IAminaDeepMemory.load(user)
        self.assertEqual(reloaded.total_interactions, 7)
        self.assertEqual(reloaded.relationship_stage, "building")


class ConversationStorePortTests(SimpleTestCase):
    def test_abc_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            ConversationStore()

    def test_register_and_get_roundtrip(self):
        original = get_conversation_store()
        try:
            class _S(ConversationStore):
                def append(self, *a): ...
                def recent(self, *a, **k): return []
                def count(self, *a): return 0
            s = _S()
            register_conversation_store(s)
            self.assertIs(get_conversation_store(), s)
        finally:
            register_conversation_store(original)


class DiabetesConversationAdapterTests(TestCase):
    """The diabetes adapter persists chat turns and returns them newest-first."""

    def test_append_recent_count_and_role_filter(self):
        user = User.objects.create(username="ports_conv")
        store = get_conversation_store()
        self.assertIsNotNone(store, "diabetes app should have registered a ConversationStore")

        store.append(user.id, "user", "first")
        store.append(user.id, "assistant", "second")
        store.append(user.id, "user", "third")

        self.assertEqual(store.count(user.id), 3)

        recent = store.recent(user.id, 10)
        self.assertEqual([t.message for t in recent], ["third", "second", "first"])  # newest-first
        self.assertIsInstance(recent[0], ChatTurn)

        only_user = store.recent(user.id, 10, role="user")
        self.assertEqual([t.message for t in only_user], ["third", "first"])

        offset = store.recent(user.id, 10, offset=1)
        self.assertEqual([t.message for t in offset], ["second", "first"])


class SeamGuardTests(SimpleTestCase):
    """Static guard: the companion package must import no module package."""

    def test_no_companion_module_imports_diabetes(self):
        companion_dir = Path(__file__).resolve().parents[2] / "companion"
        offenders = []
        pattern = re.compile(r"^\s*(from|import)\s+diabetes")
        for py in companion_dir.glob("*.py"):
            for line in py.read_text().splitlines():
                if line.strip().startswith("#"):
                    continue
                if pattern.match(line):
                    offenders.append(f"{py.name}: {line.strip()}")
        self.assertEqual(offenders, [], f"companion/ imports diabetes.*: {offenders}")

    def test_no_session_cache_or_chat_model_references(self):
        companion_dir = Path(__file__).resolve().parents[2] / "companion"
        for py in companion_dir.glob("*.py"):
            text = py.read_text()
            self.assertNotIn("session_cache", text, f"{py.name} references session_cache")
            self.assertNotIn("AIChatMessage", text, f"{py.name} references AIChatMessage")
