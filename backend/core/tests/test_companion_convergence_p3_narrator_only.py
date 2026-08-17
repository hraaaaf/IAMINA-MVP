def test_p3_chassis_conversation_has_no_diabetes_semantic_authority():
    pathlib = __import__("pathlib")
    root = pathlib.Path(__file__).resolve().parents[2]
    conversation = (root / "companion" / "conversation.py").read_text()
    state = (root / "companion" / "state.py").read_text()
    tone = (root / "companion" / "tone.py").read_text()
    prompts = (root / "companion" / "narrator_prompts.py").read_text()

    assert "def _fallback_reply" not in conversation
    assert "memory.patterns" not in conversation
    assert "think_before_reply" not in conversation
    assert "companion.prompts" not in conversation
    assert "get_companion_context" in conversation
    assert "get_offline_fallback" in conversation
    assert "GOVERNED_COMPANION_CONTEXT" in conversation

    assert "TIR_GOOD_THRESHOLD" not in tone
    assert "TIR_STRUGGLE_THRESHOLD" not in tone
    assert "CV_STABLE_THRESHOLD" not in tone
    assert "trend_direction" not in state
    assert "tir =" not in state
    assert "cv =" not in state

    lowered_prompts = prompts.lower()
    assert "patient diabétique" not in lowered_prompts
    assert "ton tir" not in lowered_prompts
    assert "diagnosis, causality, priority, treatment, dose" in prompts


def test_governed_context_block_preserves_provenance_and_limitations():
    context_module = __import__(
        "core.contracts.companion_context",
        fromlist=[
            "CompanionAfterVisit",
            "CompanionChange",
            "CompanionContext",
            "CompanionPattern",
        ],
    )
    conversation = __import__("companion.conversation", fromlist=["_companion_context_block"])

    context = context_module.CompanionContext(
        pattern_status="available",
        review_status="compared",
        review_anchor_captured_at="2026-08-17T18:00:00+00:00",
        patterns=(
            context_module.CompanionPattern(
                observation_key="observation_a",
                current_state="observed",
                markers=("marker",),
                evidence_density="high",
                recurrence_count=3,
                baseline_direction="stable",
                baseline_movement="none",
                first_observed_at="2026-08-10T18:00:00+00:00",
                last_observed_at="2026-08-17T18:00:00+00:00",
                evidence_id="evidence-1",
                source_version="pattern.v1",
                limitations=("descriptive_only",),
            ),
        ),
        changes_since_review=(
            context_module.CompanionChange(
                observation_key="observation_a",
                change_kind="unchanged",
                evidence_strength="high",
                missing_data=("none",),
                source_version="change.v1",
            ),
        ),
        after_visit=context_module.CompanionAfterVisit(
            status="recorded",
            anchor_id=9,
            occurred_at="2026-08-17T18:00:00+00:00",
            source="clinician_record",
            fact_count=2,
            latest_fact_at="2026-08-17T18:00:00+00:00",
        ),
        safety_notice="descriptive only",
        source_version="companion-overview.v1",
        language="fr",
    )

    block = conversation._companion_context_block(context)

    assert "source_version=companion-overview.v1" in block
    assert "source_version=pattern.v1" in block
    assert "limitations=descriptive_only" in block
    assert "evidence_strength=high" in block
    assert "safety_notice=descriptive only" in block
    assert "Do not infer diagnosis, causality, priority, treatment, dose" in block


def test_offline_fallback_delegates_to_active_module_contract():
    mock_module = __import__("unittest.mock", fromlist=["patch"])
    clinical = __import__("core.companion.clinical", fromlist=["get_offline_fallback"])
    domain_module = __import__(
        "core.contracts.domain_context",
        fromlist=["DomainContext"],
    )

    expected_context = domain_module.DomainContext.empty(language="fr")

    class FakeEngine:
        def offline_fallback(self, context, language="fr"):
            assert context is expected_context
            assert language == "fr"
            return "module-owned fallback"

    with mock_module.patch.object(clinical, "_resolve_engine", return_value=FakeEngine()):
        result = clinical.get_offline_fallback(42, expected_context, language="fr")

    assert result == "module-owned fallback"


def test_chat_keeps_clinical_patterns_out_of_relationship_memory():
    mock_module = __import__("unittest.mock", fromlist=["patch"])
    types_module = __import__("types")
    conversation = __import__("companion.conversation", fromlist=["chat"])
    domain_module = __import__(
        "core.contracts.domain_context",
        fromlist=["DomainContext"],
    )
    companion_module = __import__(
        "core.contracts.companion_context",
        fromlist=["CompanionContext"],
    )

    class Memory:
        patient_id = 42
        patterns = ["legacy_pattern"]
        emotional_signals = []
        last_concern = None
        milestones_celebrated = []

        def save(self):
            return None

        def _record_keyword_emotion(self, signal, concern):
            self.emotional_signals.append(signal)
            self.last_concern = concern

    class Deep:
        consecutive_log_days = 0
        total_interactions = 0
        relationship_stage = "new"
        communication_style = "unknown"
        last_log_date = None

        def save(self):
            return None

    class LLM:
        def complete(self, system, user):
            assert "GOVERNED_COMPANION_CONTEXT" in system
            assert "legacy_pattern" not in user
            return types_module.SimpleNamespace(content='{"reply":"Bonjour.","concern_detected":"clinical_alarm"}')

    patient = types_module.SimpleNamespace(id=42, first_name="")
    ctx = domain_module.DomainContext.empty(language="fr")
    governed = companion_module.CompanionContext.empty(language="fr")
    memory = Memory()

    with (
        mock_module.patch.object(conversation, "_get_context", return_value=ctx),
        mock_module.patch.object(conversation, "_get_companion_context", return_value=governed),
        mock_module.patch.object(conversation, "_recent_turns", return_value=[]),
        mock_module.patch.object(conversation, "_turn_count", return_value=0),
        mock_module.patch.object(conversation, "_append_turn"),
    ):
        reply = conversation.chat(
            "Bonjour",
            memory,
            Deep(),
            llm=LLM(),
            patient=patient,
            language="fr",
        )

    assert reply == "Bonjour."
    assert memory.patterns == ["legacy_pattern"]
    assert memory.emotional_signals == []
    assert memory.last_concern is None
