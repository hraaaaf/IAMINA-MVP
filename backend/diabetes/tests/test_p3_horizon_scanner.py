from datetime import datetime, timezone

from django.test import SimpleTestCase

from diabetes.services.clinical.evidence_horizon_contract import (
    HorizonCandidate,
    HorizonFinality,
    HorizonVerification,
)
from diabetes.services.clinical.evidence_horizon_scanner import (
    HorizonScanBatch,
    HorizonScanState,
    merge_scan_batches,
)
from diabetes.services.clinical.evidence_registry import EvidenceMaturity


class HorizonScannerContractTests(SimpleTestCase):
    def setUp(self):
        self.retrieved_at = datetime(2026, 8, 13, tzinfo=timezone.utc)

    def _candidate(self):
        return HorizonCandidate(
            topic="glycemic assessment",
            source_organization="Example Society",
            source_title="Example guidance",
            identifier="doi:10.0000/example",
            publication_or_version_date="2026-08-01",
            finality_status=HorizonFinality.FINAL,
            proposed_maturity=EvidenceMaturity.STANDARD_OF_CARE,
            population=("adults with diabetes",),
            modality=("CGM",),
            jurisdiction="international",
            regulatory_status="not_applicable",
            retrieved_at=self.retrieved_at,
            source_locator="https://example.invalid/guidance",
            verification_status=HorizonVerification.VERIFIED,
        )

    def test_complete_empty_batch_can_prove_no_updates(self):
        batch = HorizonScanBatch(
            source_key="example",
            retrieved_at=self.retrieved_at,
            state=HorizonScanState.COMPLETE,
        )
        self.assertTrue(batch.proves_no_updates)

    def test_incomplete_batch_never_proves_no_updates(self):
        batch = HorizonScanBatch(
            source_key="example",
            retrieved_at=self.retrieved_at,
            state=HorizonScanState.INCOMPLETE,
            failure_reason="timeout",
        )
        self.assertFalse(batch.proves_no_updates)

    def test_incomplete_batch_requires_reason(self):
        with self.assertRaisesRegex(ValueError, "failure_reason"):
            HorizonScanBatch(
                source_key="example",
                retrieved_at=self.retrieved_at,
                state=HorizonScanState.INCOMPLETE,
            )

    def test_candidate_timestamp_must_match_batch(self):
        candidate = self._candidate()
        with self.assertRaisesRegex(ValueError, "timestamp"):
            HorizonScanBatch(
                source_key="example",
                retrieved_at=datetime(2026, 8, 14, tzinfo=timezone.utc),
                state=HorizonScanState.COMPLETE,
                candidates=(candidate,),
            )

    def test_merge_preserves_candidates_and_incomplete_state(self):
        candidate = self._candidate()
        complete = HorizonScanBatch(
            source_key="one",
            retrieved_at=self.retrieved_at,
            state=HorizonScanState.COMPLETE,
            candidates=(candidate,),
        )
        incomplete = HorizonScanBatch(
            source_key="two",
            retrieved_at=self.retrieved_at,
            state=HorizonScanState.INCOMPLETE,
            failure_reason="unreachable",
        )
        merged = merge_scan_batches(complete, incomplete)
        self.assertEqual(merged.state, HorizonScanState.INCOMPLETE)
        self.assertEqual(merged.candidates, (candidate,))
        self.assertIn("two: unreachable", merged.failure_reason)
        self.assertFalse(merged.proves_no_updates)

    def test_merge_requires_shared_retrieval_timestamp(self):
        first = HorizonScanBatch(
            source_key="one",
            retrieved_at=self.retrieved_at,
            state=HorizonScanState.COMPLETE,
        )
        second = HorizonScanBatch(
            source_key="two",
            retrieved_at=datetime(2026, 8, 14, tzinfo=timezone.utc),
            state=HorizonScanState.COMPLETE,
        )
        with self.assertRaisesRegex(ValueError, "share one retrieval timestamp"):
            merge_scan_batches(first, second)
