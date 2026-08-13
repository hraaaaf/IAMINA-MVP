from types import SimpleNamespace

from django.test import SimpleTestCase

from diabetes.services.clinical.evidence_horizon_certification import (
    HorizonCertificationStatus,
    certify_horizon_batch,
)
from diabetes.services.clinical.evidence_horizon_contract import HorizonFinality, HorizonVerification
from diabetes.services.clinical.evidence_horizon_scanner import HorizonScanState


class HorizonCertificationContractTests(SimpleTestCase):
    def _batch(self, *, state, verification, finality, identifier="id:1"):
        item = SimpleNamespace(
            verification_status=verification,
            finality_status=finality,
            identifier=identifier,
        )
        return SimpleNamespace(state=state, candidates=(item,))

    def test_state_matrix(self):
        ok = self._batch(
            state=HorizonScanState.COMPLETE,
            verification=list(HorizonVerification)[1],
            finality=list(HorizonFinality)[0],
        )
        self.assertEqual(certify_horizon_batch(ok).status, HorizonCertificationStatus.PASS)

        partial = SimpleNamespace(state=HorizonScanState.INCOMPLETE, candidates=())
        self.assertEqual(
            certify_horizon_batch(partial).status,
            HorizonCertificationStatus.INCOMPLETE,
        )

        needs_review = self._batch(
            state=HorizonScanState.COMPLETE,
            verification=list(HorizonVerification)[0],
            finality=list(HorizonFinality)[0],
        )
        self.assertEqual(
            certify_horizon_batch(needs_review).status,
            HorizonCertificationStatus.REVIEW_REQUIRED,
        )
