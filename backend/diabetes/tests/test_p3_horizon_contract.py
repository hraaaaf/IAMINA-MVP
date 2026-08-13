from datetime import datetime, timezone

from django.test import SimpleTestCase

from diabetes.services.clinical.evidence_horizon_contract import (
    HorizonCandidate,
    HorizonFinality,
    HorizonVerification,
)
from diabetes.services.clinical.evidence_registry import EvidenceMaturity


class HorizonCandidateContractTests(SimpleTestCase):
    def _candidate(self, **overrides):
        values = {
            "topic": "glycemic assessment",
            "source_organization": "Example Society",
            "source_title": "Example final guidance",
            "identifier": "doi:10.0000/example",
            "publication_or_version_date": "2026-08-01",
            "finality_status": HorizonFinality.FINAL,
            "proposed_maturity": EvidenceMaturity.STANDARD_OF_CARE,
            "population": ("adults with diabetes",),
            "modality": ("CGM",),
            "jurisdiction": "international",
            "regulatory_status": "not_applicable",
            "retrieved_at": datetime(2026, 8, 13, tzinfo=timezone.utc),
            "source_locator": "https://example.invalid/guidance",
            "verification_status": HorizonVerification.VERIFIED,
        }
        values.update(overrides)
        return HorizonCandidate(**values)

    def test_verified_final_candidate_can_enter_review_queue(self):
        candidate = self._candidate()
        self.assertTrue(candidate.eligible_for_registry_review)
        self.assertEqual(len(candidate.candidate_fingerprint), 64)

    def test_draft_never_becomes_registry_review_eligible(self):
        candidate = self._candidate(finality_status=HorizonFinality.DRAFT)
        self.assertFalse(candidate.eligible_for_registry_review)

    def test_unverified_candidate_never_becomes_registry_review_eligible(self):
        candidate = self._candidate(verification_status=HorizonVerification.UNVERIFIED)
        self.assertFalse(candidate.eligible_for_registry_review)

    def test_verified_candidate_requires_canonical_identifier(self):
        with self.assertRaisesRegex(ValueError, "canonical identifier"):
            self._candidate(identifier="")

    def test_internal_governed_rule_maturity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "internal governed rules"):
            self._candidate(proposed_maturity=EvidenceMaturity.INTERNAL_GOVERNED_RULE)

    def test_retrieval_time_must_be_timezone_aware(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self._candidate(retrieved_at=datetime(2026, 8, 13))

    def test_fingerprint_is_stable_for_equivalent_identity(self):
        first = self._candidate(source_title="  Example Final Guidance ")
        second = self._candidate(source_title="example final guidance")
        self.assertEqual(first.candidate_fingerprint, second.candidate_fingerprint)
