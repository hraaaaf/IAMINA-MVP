from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from diabetes.services.clinical.evidence_registry import ClinicalAuthority
from diabetes.services.clinical.proactive_attention import (
    EmergencyClearance,
    select_next_proactive_insight,
)


class ProactiveEvidenceAuthorityTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="p2-proactive-evidence")

    @patch("diabetes.services.clinical.proactive_attention.refresh_personal_response_memory")
    @patch("diabetes.services.clinical.proactive_attention.get_evidence")
    def test_non_governed_rule_stops_before_clinical_twin_refresh(
        self,
        get_evidence,
        refresh_memory,
    ):
        get_evidence.return_value = SimpleNamespace(
            clinical_authority=ClinicalAuthority.REFERENCE_ONLY,
            supersession_state="current",
        )

        decision = select_next_proactive_insight(
            patient_id=self.patient.id,
            emergency_clearance=EmergencyClearance.CLEAR,
        )

        self.assertIsNone(decision.candidate)
        self.assertEqual(decision.suppression_reason, "source_rule_not_governed")
        refresh_memory.assert_not_called()

    @patch("diabetes.services.clinical.proactive_attention.refresh_personal_response_memory")
    @patch("diabetes.services.clinical.proactive_attention.get_evidence")
    def test_superseded_rule_stops_before_clinical_twin_refresh(
        self,
        get_evidence,
        refresh_memory,
    ):
        get_evidence.return_value = SimpleNamespace(
            clinical_authority=ClinicalAuthority.GOVERNED_RULE,
            supersession_state="superseded",
        )

        decision = select_next_proactive_insight(
            patient_id=self.patient.id,
            emergency_clearance=EmergencyClearance.CLEAR,
        )

        self.assertIsNone(decision.candidate)
        self.assertEqual(decision.suppression_reason, "source_rule_superseded")
        refresh_memory.assert_not_called()
