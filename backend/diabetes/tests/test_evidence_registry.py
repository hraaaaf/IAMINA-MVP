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

    def test_gmi_rule_requires_verified_cgm_and_is_not_lab_a1c(self):
        record = get_evidence("rule.metric.gmi-cgm.v1")
        combined = " ".join((record.claim_or_rule, record.limitations)).lower()
        self.assertIn("cgm", combined)
        self.assertIn("verified", combined)
        self.assertIn("not laboratory a1c", combined)

    def test_hyperglycemia_product_thresholds_are_not_mislabeled_standard_of_care(self):
        record = evidence_for_alert("hyperglycemia_critical")
        self.assertEqual(record.evidence_maturity, EvidenceMaturity.INTERNAL_GOVERNED_RULE)
        self.assertEqual(record.supporting_evidence_ids, ())
        combined = " ".join((record.claim_or_rule, record.limitations)).lower()
        self.assertIn("product", combined)
        self.assertIn("not diagnostic", combined)
        self.assertIn("not universal", combined)
