"""P1-EVIDENCE — immutable diabetes evidence registry regression gates."""
from django.test import SimpleTestCase

from diabetes.services.clinical.evidence_registry import (
    ALERT_EVIDENCE_IDS,
    EVIDENCE_REGISTRY,
    KPI_EVIDENCE_IDS,
    PATTERN_EVIDENCE_IDS,
    PERSONAL_RESPONSE_EVIDENCE_ID,
    ClinicalAuthority,
    EvidenceMaturity,
    FinalityStatus,
    RecordKind,
    evidence_for_alert,
    evidence_for_kpi,
    evidence_for_pattern,
    get_evidence,
    validate_registry,
)


class EvidenceRegistryInvariantTests(SimpleTestCase):
    def test_registry_is_valid(self):
        self.assertEqual(validate_registry(), ())

    def test_unknown_evidence_id_fails_closed(self):
        with self.assertRaises(KeyError):
            get_evidence("rule.not-real.v1")

    def test_standard_of_care_sources_are_final(self):
        standard_sources = [
            record
            for record in EVIDENCE_REGISTRY.values()
            if record.evidence_maturity == EvidenceMaturity.STANDARD_OF_CARE
        ]
        self.assertTrue(standard_sources)
        self.assertTrue(
            all(record.finality_status == FinalityStatus.FINAL for record in standard_sources)
        )

    def test_external_sources_never_hold_runtime_rule_authority(self):
        source_records = [
            record for record in EVIDENCE_REGISTRY.values() if record.kind == RecordKind.SOURCE
        ]
        self.assertTrue(source_records)
        self.assertTrue(
            all(record.clinical_authority == ClinicalAuthority.NONE for record in source_records)
        )

    def test_internal_rules_are_separate_from_external_evidence_maturity(self):
        rule_records = [
            record for record in EVIDENCE_REGISTRY.values() if record.kind == RecordKind.RULE
        ]
        self.assertTrue(rule_records)
        self.assertTrue(
            all(
                record.evidence_maturity == EvidenceMaturity.INTERNAL_GOVERNED_RULE
                for record in rule_records
            )
        )

    def test_regulatory_status_is_explicit_and_orthogonal(self):
        for record in EVIDENCE_REGISTRY.values():
            self.assertTrue(record.regulatory_status)
        ada = get_evidence("source.ada.2026.section6")
        self.assertEqual(ada.regulatory_status, "not_applicable")
        self.assertEqual(ada.evidence_maturity, EvidenceMaturity.STANDARD_OF_CARE)

    def test_phnh_source_metadata_matches_published_record(self):
        phnh = get_evidence("source.gonzalez-vidal.2025.phnh")
        self.assertEqual(
            phnh.source_title,
            "Post-hypoglycemic nocturnal hyperglycemia in type 1 diabetes: "
            "the Somogyi hypothesis revisited",
        )
        self.assertEqual(
            phnh.identifier,
            "DOI 10.1007/s42000-025-00680-0; PMID 40465171",
        )
        self.assertEqual(phnh.evidence_maturity, EvidenceMaturity.EMERGING_EVIDENCE)
        self.assertEqual(phnh.clinical_authority, ClinicalAuthority.NONE)

    def test_metadata_contains_required_acceptance_fields(self):
        metadata = get_evidence("rule.metric.gmi-cgm.v1").to_metadata()
        for field in (
            "evidence_id",
            "evidence_maturity",
            "publication_or_version_date",
            "finality_status",
            "population",
            "modality",
            "reviewed_at",
            "supersession_state",
            "clinical_authority",
            "regulatory_status",
            "reviewer",
            "next_review_at",
            "assumptions",
            "exclusions",
        ):
            self.assertIn(field, metadata)
        self.assertEqual(metadata["supersession_state"], "current")

    def test_all_registry_links_resolve(self):
        for record in EVIDENCE_REGISTRY.values():
            for evidence_id in (
                *record.supporting_evidence_ids,
                *record.supersedes,
                *record.superseded_by,
            ):
                self.assertIn(evidence_id, EVIDENCE_REGISTRY)


class RuntimeEvidenceCoverageTests(SimpleTestCase):
    def test_all_declared_kpis_resolve_to_versioned_records(self):
        self.assertGreaterEqual(len(KPI_EVIDENCE_IDS), 10)
        for metric_name in KPI_EVIDENCE_IDS:
            self.assertEqual(evidence_for_kpi(metric_name).evidence_id, KPI_EVIDENCE_IDS[metric_name])

    def test_all_declared_pattern_codes_resolve_to_versioned_records(self):
        self.assertGreaterEqual(len(PATTERN_EVIDENCE_IDS), 10)
        for pattern_code in PATTERN_EVIDENCE_IDS:
            self.assertEqual(
                evidence_for_pattern(pattern_code).evidence_id,
                PATTERN_EVIDENCE_IDS[pattern_code],
            )

    def test_alert_threshold_families_are_registered(self):
        self.assertEqual(set(ALERT_EVIDENCE_IDS), {
            "hypoglycemia_level2",
            "hypoglycemia_level1",
            "hyperglycemia_critical",
            "hyperglycemia_repeated",
        })
        for alert_code in ALERT_EVIDENCE_IDS:
            self.assertEqual(evidence_for_alert(alert_code).evidence_id, ALERT_EVIDENCE_IDS[alert_code])

    def test_personal_response_rule_is_registered(self):
        record = get_evidence(PERSONAL_RESPONSE_EVIDENCE_ID)
        self.assertEqual(record.kind, RecordKind.RULE)
        self.assertEqual(record.clinical_authority, ClinicalAuthority.GOVERNED_RULE)

    def test_gmi_sources_are_peer_reviewed_evidence_not_automatic_standard_of_care(self):
        legacy = get_evidence("source.bergenstal.2018.gmi")
        updated = get_evidence("source.bergenstal.2026.ugmi")
        rule = get_evidence("rule.metric.gmi-cgm.v1")

        self.assertEqual(legacy.evidence_maturity, EvidenceMaturity.EMERGING_EVIDENCE)
        self.assertEqual(updated.evidence_maturity, EvidenceMaturity.EMERGING_EVIDENCE)
        self.assertEqual(updated.clinical_authority, ClinicalAuthority.NONE)
        self.assertEqual(rule.clinical_authority, ClinicalAuthority.GOVERNED_RULE_CANDIDATE)
        self.assertIn(updated.evidence_id, rule.supporting_evidence_ids)

    def test_gmi_rule_requires_verified_cgm_and_formula_promotion(self):
        record = get_evidence("rule.metric.gmi-cgm.v1")
        combined = " ".join((record.claim_or_rule, record.limitations)).lower()
        modality = " ".join(record.modality).lower()
        self.assertIn("cgm", combined)
        self.assertIn("verified", modality)
        self.assertIn("promotion", combined)
        self.assertIn("not laboratory a1c", combined)

    def test_hyperglycemia_product_thresholds_are_not_mislabeled_standard_of_care(self):
        record = evidence_for_alert("hyperglycemia_critical")
        self.assertEqual(record.evidence_maturity, EvidenceMaturity.INTERNAL_GOVERNED_RULE)
        self.assertEqual(record.supporting_evidence_ids, ())
        combined = " ".join((record.claim_or_rule, record.limitations)).lower()
        self.assertIn("product", combined)
        self.assertIn("not diagnostic", combined)
        self.assertIn("do not present 250/300 mg/dl as universal", combined)


def test_symptom_triage_rule_has_cross_checked_standard_sources():
    nice = get_evidence("source.nice.ng17.dka")
    rule = get_evidence("rule.triage.symptom-professional-escalation.v1")

    assert nice.kind == RecordKind.SOURCE
    assert nice.evidence_maturity == EvidenceMaturity.STANDARD_OF_CARE
    assert nice.clinical_authority == ClinicalAuthority.NONE
    assert rule.kind == RecordKind.RULE
    assert rule.clinical_authority == ClinicalAuthority.GOVERNED_RULE
    assert set(rule.supporting_evidence_ids) == {
        "source.ada.2026.section6",
        "source.nice.ng17.dka",
    }



def test_clinician_prep_rule_is_registered_as_governed_product_rule():
    rule = get_evidence("rule.consultation.preparation.v1")
    assert rule.kind == RecordKind.RULE
    assert rule.clinical_authority == ClinicalAuthority.GOVERNED_RULE
    assert "review support" in rule.limitations.lower()
    assert "treatment change" in rule.limitations.lower()



def test_all_runtime_rules_have_structured_review_governance():
    rules = [
        record
        for record in EVIDENCE_REGISTRY.values()
        if record.kind == RecordKind.RULE
    ]
    assert rules
    for record in rules:
        assert record.reviewer == "IAmina Clinical Governance"
        assert record.next_review_at == "2027-02-12"
        assert record.assumptions
        assert record.exclusions
        assert record.next_review_at > record.reviewed_at


def test_runtime_rule_metadata_exposes_review_governance():
    metadata = get_evidence("rule.personal-response.repetition.v1").to_metadata()
    assert metadata["reviewer"] == "IAmina Clinical Governance"
    assert metadata["next_review_at"] == "2027-02-12"
    assert metadata["assumptions"] == [
        "declared population and modality applicability are satisfied"
    ]
    assert metadata["exclusions"] == [
        "use outside the declared population or modality without separate review"
    ]


def test_registry_validation_rejects_missing_rule_governance(monkeypatch):
    source = get_evidence("rule.personal-response.repetition.v1")
    broken = type(source)(
        evidence_id=source.evidence_id,
        kind=source.kind,
        topic=source.topic,
        claim_or_rule=source.claim_or_rule,
        evidence_maturity=source.evidence_maturity,
        source_organization=source.source_organization,
        source_title=source.source_title,
        identifier=source.identifier,
        publication_or_version_date=source.publication_or_version_date,
        finality_status=source.finality_status,
        population=source.population,
        modality=source.modality,
        jurisdiction=source.jurisdiction,
        regulatory_status=source.regulatory_status,
        reviewed_at=source.reviewed_at,
        clinical_authority=source.clinical_authority,
        limitations=source.limitations,
        reviewer="",
        next_review_at="2026-01-01",
        assumptions=(),
        exclusions=(),
        supporting_evidence_ids=source.supporting_evidence_ids,
    )

    import diabetes.services.clinical.evidence_registry as registry

    monkeypatch.setattr(
        registry,
        "_RECORDS",
        tuple(
            broken if record.evidence_id == broken.evidence_id else record
            for record in registry._RECORDS
        ),
    )
    monkeypatch.setattr(
        registry,
        "EVIDENCE_REGISTRY",
        {record.evidence_id: record for record in registry._RECORDS},
    )
    errors = registry.validate_registry()
    assert f"{broken.evidence_id}: reviewer missing" in errors
    assert f"{broken.evidence_id}: assumptions missing" in errors
    assert f"{broken.evidence_id}: exclusions missing" in errors
    assert f"{broken.evidence_id}: next_review_at must be after reviewed_at" in errors
