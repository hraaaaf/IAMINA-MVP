from django.test import SimpleTestCase

from diabetes.services.clinical.evidence_horizon_certification import (
    HorizonCertificationStatus,
    certify_horizon_batch,
)


class HorizonCertificationContractTests(SimpleTestCase):
    def test_public_status_contract_is_stable(self):
        self.assertEqual(
            {item.value for item in HorizonCertificationStatus},
            {"pass", "review_required", "incomplete"},
        )

    def test_public_certifier_is_callable(self):
        self.assertTrue(callable(certify_horizon_batch))
