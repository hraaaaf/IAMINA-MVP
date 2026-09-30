import json
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.domain_context import DomainContext


class ProtectedShadowRealDataBoundaryCommandTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="internal-boundary-auditor",
            password="unused",
            is_active=True,
            is_staff=True,
        )

    def _resolution(self):
        return AdviceResolution(
            decision=AdviceDecision(
                intent="clinician_prep",
                authority_level=AdviceAuthorityLevel.L1_EDUCATION,
                decision=AdviceDisposition.CONSTRAIN,
                rule_id="diabetes.clinician_prep.real-boundary-test",
                rule_version="1",
                allowed_actions=("prepare_clinician_questions",),
                forbidden_actions=("diagnose", "change_treatment"),
                required_facts=("certified_consultation_brief",),
                language="fr",
            ),
            reply="Corps clinique local 142 mg/dL, jamais destiné au provider.",
        )

    def test_real_data_boundary_audit_never_calls_provider_or_policy(self):
        out = StringIO()
        resolution = self._resolution()

        with (
            patch(
                "core.management.commands.audit_protected_shadow_real_data_boundary."
                "get_domain_context",
                return_value=DomainContext.empty(language="fr"),
            ),
            patch(
                "core.management.commands.audit_protected_shadow_real_data_boundary."
                "get_advice_resolution",
                return_value=resolution,
            ),
            patch(
                "core.management.commands.audit_protected_shadow_real_data_boundary."
                "verify_protected_advice_reply",
                side_effect=lambda _pid, _resolution, candidate: candidate,
            ),
            patch(
                "companion.protected_provider_shadow.authorize_processor_policy"
            ) as authorize,
            patch(
                "companion.protected_provider_shadow.build_openai_compatible_provider"
            ) as build_provider,
        ):
            call_command(
                "audit_protected_shadow_real_data_boundary",
                patient_id=self.patient.id,
                language="fr",
                stdout=out,
            )

        payload = json.loads(out.getvalue())
        assert payload["status"] == "pass"
        assert payload["provider_call_performed"] is False
        assert payload["processor_policy_bypassed"] is False
        assert payload["deterministic_body_in_provider_payload"] is False
        assert payload["trigger_in_provider_payload"] is False
        assert payload["local_reinjection_verified"] is True
        assert payload["module_verifier_passed"] is True
        assert payload["payload_fields"] == [
            "locale",
            "script",
            "protected_body_token",
        ]
        authorize.assert_not_called()
        build_provider.assert_not_called()

    def test_non_staff_patient_is_rejected_before_clinical_resolution(self):
        self.patient.is_staff = False
        self.patient.save(update_fields=["is_staff"])

        with patch(
            "core.management.commands.audit_protected_shadow_real_data_boundary."
            "get_domain_context"
        ) as get_context:
            try:
                call_command(
                    "audit_protected_shadow_real_data_boundary",
                    patient_id=self.patient.id,
                    stdout=StringIO(),
                )
            except Exception as exc:
                assert "active staff accounts" in str(exc)
            else:
                raise AssertionError("non-staff patient should be rejected")

        get_context.assert_not_called()
