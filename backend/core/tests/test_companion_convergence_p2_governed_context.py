def test_chassis_resolver_has_no_diabetes_dependency():
    pathlib = __import__("pathlib")
    root = pathlib.Path(__file__).resolve().parents[2]
    source = (root / "core" / "companion" / "clinical.py").read_text()

    assert "diabetes" not in source.lower()
    assert "engine.companion_context" in source


def test_base_engine_default_companion_context_is_neutral():
    abc_module = __import__("core.engine.base", fromlist=["BaseEngine"])
    domain_module = __import__(
        "core.contracts.domain_context",
        fromlist=["DomainContext"],
    )

    class MinimalEngine(abc_module.BaseEngine):
        def analyze(self, patient_id, language="fr", days=14):
            return domain_module.DomainContext.empty(language=language)

    context = MinimalEngine().companion_context(7, language="ar-MA")

    assert context.pattern_status == "unavailable"
    assert context.review_status == "unavailable"
    assert context.patterns == ()
    assert context.language == "ar-MA"


def test_chassis_companion_context_delegates_to_active_engine():
    mock_module = __import__("unittest.mock", fromlist=["patch"])
    context_module = __import__(
        "core.contracts.companion_context",
        fromlist=["CompanionContext"],
    )
    clinical = __import__("core.companion.clinical", fromlist=["get_companion_context"])

    expected = context_module.CompanionContext.empty(language="en")

    class FakeEngine:
        def companion_context(self, patient_id, language="fr"):
            assert patient_id == 42
            assert language == "en"
            return expected

    with mock_module.patch.object(clinical, "_resolve_engine", return_value=FakeEngine()):
        result = clinical.get_companion_context(42, language="en")

    assert result is expected


def test_diabetes_engine_adapts_certified_overview_without_raw_models():
    datetime_module = __import__("datetime")
    mock_module = __import__("unittest.mock", fromlist=["patch"])
    types_module = __import__("types")
    engine_module = __import__(
        "diabetes.services.clinical.evidence_engine",
        fromlist=["EvidenceGuardedDiabetesEngine"],
    )

    moment = datetime_module.datetime(
        2026,
        8,
        17,
        18,
        0,
        tzinfo=datetime_module.timezone.utc,
    )
    pattern = types_module.SimpleNamespace(
        observation_key="stable_pattern",
        current_state="observed",
        markers=("marker_a",),
        evidence_density="high",
        recurrence_count=3,
        baseline_direction="stable",
        baseline_movement="none",
        first_observed_at=moment,
        last_observed_at=moment,
        evidence_id="evidence-1",
        source_version="pattern.v1",
        limitations=("descriptive_only",),
    )
    change = types_module.SimpleNamespace(
        observation_key="stable_pattern",
        change_kind="unchanged",
        evidence_strength="high",
        missing_data=(),
        source_version="change.v1",
    )
    after_visit = types_module.SimpleNamespace(
        status="recorded",
        anchor_id=9,
        occurred_at=moment,
        source="clinician_record",
        fact_count=2,
        latest_fact_at=moment,
    )
    overview = types_module.SimpleNamespace(
        pattern_status="available",
        review_status="compared",
        review_anchor_captured_at=moment,
        patterns=(pattern,),
        changes_since_review=(change,),
        after_visit=after_visit,
        safety_notice="descriptive only",
        source_version="companion-overview.v1",
    )

    with mock_module.patch.object(
        engine_module,
        "build_companion_overview",
        return_value=overview,
    ) as builder:
        context = engine_module.EvidenceGuardedDiabetesEngine().companion_context(
            42,
            language="fr",
        )

    builder.assert_called_once_with(patient_id=42)
    assert context.patterns[0].evidence_id == "evidence-1"
    assert context.patterns[0].first_observed_at == moment.isoformat()
    assert context.changes_since_review[0].change_kind == "unchanged"
    assert context.after_visit.anchor_id == 9
    assert context.source_version == "companion-overview.v1"
    assert context.language == "fr"
