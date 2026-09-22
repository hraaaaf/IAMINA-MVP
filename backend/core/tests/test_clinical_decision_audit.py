from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from companion import conversation
from core.clinical_decision_audit import (
    AUDIT_SCHEMA_VERSION,
    clinical_decision_audit_metadata,
    clinician_audit_detail,
    record_clinical_decision_audit,
)
from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.domain_context import DomainContext
from core.models import AuditLog


def _resolution() -> AdviceResolution:
    return AdviceResolution(
        decision=AdviceDecision(
            intent="monitoring_interpretation",
            authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.monitoring.interpretation",
            rule_version="1",
            allowed_actions=("explain_recorded_glucose_context",),
            forbidden_actions=("change_treatment",),
            required_facts=("latest_glucose", "measurement_source"),
            missing_facts=("measurement_source",),
            evidence_refs=("rule.metric.recorded-glucose-stats.v1",),
            limitations=("recorded_values_only",),
        ),
        reply="Réponse déterministe gouvernée.",
    )


class ClinicalDecisionAuditTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="ci9-audit")

    def test_metadata_is_reconstructible_without_reply_content(self):
        decision = _resolution().decision
        metadata = clinical_decision_audit_metadata(
            decision=decision,
            verifier_status="passed",
            final_reply="Réponse déterministe gouvernée.",
        )

        self.assertEqual(metadata["schema_version"], AUDIT_SCHEMA_VERSION)
        self.assertEqual(metadata["rule_id"], decision.rule_id)
        self.assertEqual(metadata["rule_version"], "1")
        self.assertEqual(metadata["authority_level"], "L2")
        self.assertEqual(metadata["disposition"], "constrain")
        self.assertEqual(
            metadata["required_fact_keys"],
            ["latest_glucose", "measurement_source"],
        )
        self.assertEqual(metadata["used_fact_keys"], ["latest_glucose"])
        self.assertEqual(metadata["missing_fact_keys"], ["measurement_source"])
        self.assertEqual(metadata["verifier_status"], "passed")
        self.assertEqual(
            metadata["constraints_applied"],
            {
                "allowed_actions": ["explain_recorded_glucose_context"],
                "forbidden_actions": ["change_treatment"],
                "limitations": ["recorded_values_only"],
            },
        )
        self.assertEqual(
            metadata["final_reply_sha256"],
            sha256("Réponse déterministe gouvernée.".encode("utf-8")).hexdigest(),
        )
        self.assertNotIn("reply", metadata)
        self.assertNotIn("Réponse déterministe gouvernée.", str(metadata))

    def test_persisted_audit_uses_existing_audit_log(self):
        entry = record_clinical_decision_audit(
            patient=self.patient,
            decision=_resolution().decision,
            verifier_status="passed",
            final_reply="Réponse déterministe gouvernée.",
        )

        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertEqual(entry.actor, self.patient)
        self.assertEqual(entry.action, "create")
        self.assertEqual(entry.resource_type, "ClinicalAdviceDecision")
        self.assertEqual(
            entry.resource_id,
            "diabetes.monitoring.interpretation@1",
        )
        self.assertEqual(entry.metadata["verifier_status"], "passed")

    def test_invalid_verifier_status_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unsupported verifier_status"):
            clinical_decision_audit_metadata(
                decision=_resolution().decision,
                verifier_status="unknown",
                final_reply="x",
            )

    @patch("companion.conversation.record_clinical_decision_audit")
    @patch("companion.conversation.verify_advice_reply")
    @patch("companion.conversation.get_advice_resolution")
    @patch("companion.conversation._get_context")
    @patch("companion.conversation._append_turn")
    @patch("companion.conversation.record_companion_route")
    def test_chat_audits_verified_governed_reply_before_return(
        self,
        route,
        _append,
        get_context,
        get_resolution,
        verify,
        audit,
    ):
        patient = SimpleNamespace(id=42, first_name="")
        resolution = _resolution()
        get_context.return_value = DomainContext.empty(language="fr")
        get_resolution.return_value = resolution
        verify.return_value = resolution.reply

        reply = conversation.chat(
            "Explique-moi cette glycémie",
            memory=None,
            deep=SimpleNamespace(save=lambda: None),
            llm=object(),
            language="fr",
            patient=patient,
        )

        self.assertEqual(reply, resolution.reply)
        audit.assert_called_once_with(
            patient=patient,
            decision=resolution.decision,
            verifier_status="passed",
            final_reply=resolution.reply,
        )
        route.assert_called_once_with("policy_rule")

    @patch("companion.conversation.record_clinical_decision_audit")
    @patch("companion.conversation.verify_advice_reply")
    @patch("companion.conversation.get_advice_resolution")
    @patch("companion.conversation._get_context")
    @patch("companion.conversation._append_turn")
    @patch("companion.conversation.record_companion_route")
    def test_stream_audits_verified_governed_reply_before_emit(
        self,
        route,
        _append,
        get_context,
        get_resolution,
        verify,
        audit,
    ):
        patient = SimpleNamespace(id=42, first_name="")
        resolution = _resolution()
        get_context.return_value = DomainContext.empty(language="fr")
        get_resolution.return_value = resolution
        verify.return_value = resolution.reply

        chunks = list(
            conversation.stream_chat(
                "Explique-moi cette glycémie",
                memory=None,
                deep=SimpleNamespace(save=lambda: None),
                llm=object(),
                language="fr",
                patient=patient,
            )
        )

        self.assertEqual(chunks, [resolution.reply])
        audit.assert_called_once_with(
            patient=patient,
            decision=resolution.decision,
            verifier_status="passed",
            final_reply=resolution.reply,
        )
        route.assert_called_once_with("policy_rule")


    def test_clinician_detail_reconstructs_complete_decision_basis(self):
        entry = record_clinical_decision_audit(
            patient=self.patient,
            decision=_resolution().decision,
            verifier_status="passed",
            final_reply="Réponse déterministe gouvernée.",
        )
        assert entry is not None

        detail = clinician_audit_detail(entry)

        self.assertEqual(detail["rule_id"], "diabetes.monitoring.interpretation")
        self.assertEqual(detail["rule_version"], "1")
        self.assertEqual(detail["authority_level"], "L2")
        self.assertEqual(detail["used_fact_keys"], ["latest_glucose"])
        self.assertEqual(detail["missing_fact_keys"], ["measurement_source"])
        self.assertEqual(detail["verifier_status"], "passed")
        self.assertIn("constraints_applied", detail)
        self.assertIn("evidence_refs", detail)

    def test_clinician_detail_rejects_non_clinical_audit_entry(self):
        entry = AuditLog.objects.create(
            actor=self.patient,
            action="view",
            resource_type="OtherResource",
            metadata={},
        )
        with self.assertRaisesRegex(ValueError, "not a clinical advice audit entry"):
            clinician_audit_detail(entry)

    @patch("companion.conversation.record_clinical_decision_audit")
    @patch("companion.conversation.verify_advice_reply")
    @patch("companion.conversation.get_advice_resolution")
    @patch("companion.conversation._get_context")
    @patch("companion.conversation._append_turn")
    @patch("companion.conversation.record_companion_route")
    def test_audit_persistence_failure_fails_closed_before_governed_reply(
        self,
        route,
        _append,
        get_context,
        get_resolution,
        verify,
        audit,
    ):
        patient = SimpleNamespace(id=42, first_name="")
        resolution = _resolution()
        get_context.return_value = DomainContext.empty(language="fr")
        get_resolution.return_value = resolution
        verify.return_value = resolution.reply
        audit.side_effect = RuntimeError("audit unavailable")

        reply = conversation.chat(
            "Explique-moi cette glycémie",
            memory=None,
            deep=SimpleNamespace(save=lambda: None),
            llm=object(),
            language="fr",
            patient=patient,
        )

        self.assertNotEqual(reply, resolution.reply)
        route.assert_called_once_with("policy_denied")
        self.assertGreaterEqual(audit.call_count, 1)
