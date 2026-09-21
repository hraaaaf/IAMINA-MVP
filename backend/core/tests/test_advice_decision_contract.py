"""Contract tests for governed clinical-advice authorization."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest import TestCase

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.capabilities import Authority


class AdviceDecisionContractTests(TestCase):
    def test_l2_authorized_action_requires_evidence_and_is_queryable(self):
        decision = AdviceDecision(
            intent="food_decision",
            authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            decision=AdviceDisposition.CONSTRAIN,
            rule_id="diabetes.food.001",
            rule_version="1",
            allowed_actions=("explain_portion_and_carbohydrate_context",),
            forbidden_actions=("approve_food_personally",),
            evidence_refs=("ada.2026.nutrition",),
        )

        self.assertTrue(
            decision.is_action_allowed("explain_portion_and_carbohydrate_context")
        )
        self.assertFalse(decision.is_action_allowed("approve_food_personally"))

    def test_generative_model_cannot_issue_advice_decision(self):
        with self.assertRaises(PermissionError):
            AdviceDecision(
                intent="food_decision",
                authority_level=AdviceAuthorityLevel.L1_EDUCATION,
                decision=AdviceDisposition.ALLOW,
                rule_id="diabetes.food.001",
                rule_version="1",
                issued_by=Authority.GENERATIVE_MODEL,
            )

    def test_l5_cannot_allow_patient_facing_action(self):
        with self.assertRaises(ValueError):
            AdviceDecision(
                intent="insulin_dose",
                authority_level=AdviceAuthorityLevel.L5_PROHIBITED,
                decision=AdviceDisposition.ALLOW,
                rule_id="core.prohibited.insulin_dose",
                rule_version="1",
                allowed_actions=("calculate_insulin_dose",),
            )

    def test_l4_requires_explicit_escalation(self):
        with self.assertRaises(ValueError):
            AdviceDecision(
                intent="treatment_change",
                authority_level=AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION,
                decision=AdviceDisposition.CONSTRAIN,
                rule_id="core.professional_validation",
                rule_version="1",
            )

        valid = AdviceDecision(
            intent="treatment_change",
            authority_level=AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION,
            decision=AdviceDisposition.ESCALATE,
            rule_id="core.professional_validation",
            rule_version="1",
            escalation="clinician_review",
        )
        self.assertFalse(valid.can_narrate_patient_action)

    def test_l3_rejects_missing_patient_facts(self):
        with self.assertRaises(ValueError):
            AdviceDecision(
                intent="contextual_recommendation",
                authority_level=AdviceAuthorityLevel.L3_CONTEXTUAL_CLINICAL,
                decision=AdviceDisposition.CONSTRAIN,
                rule_id="diabetes.context.001",
                rule_version="1",
                allowed_actions=("contextualize_pattern",),
                required_facts=("recent_cgm",),
                missing_facts=("recent_cgm",),
                evidence_refs=("ada.2026.cgm",),
            )

    def test_l2_l3_allowed_advice_requires_evidence_reference(self):
        with self.assertRaises(ValueError):
            AdviceDecision(
                intent="activity_context",
                authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
                decision=AdviceDisposition.ALLOW,
                rule_id="diabetes.activity.001",
                rule_version="1",
                allowed_actions=("explain_activity_context",),
            )

    def test_allowed_and_forbidden_actions_cannot_overlap(self):
        with self.assertRaises(ValueError):
            AdviceDecision(
                intent="food_decision",
                authority_level=AdviceAuthorityLevel.L1_EDUCATION,
                decision=AdviceDisposition.CONSTRAIN,
                rule_id="diabetes.food.001",
                rule_version="1",
                allowed_actions=("explain",),
                forbidden_actions=("explain",),
            )

    def test_untrusted_invalid_payload_fails_closed(self):
        decision = AdviceDecision.from_mapping_fail_closed(
            {
                "intent": "insulin_dose",
                "authority_level": "L5",
                "decision": "allow",
                "rule_id": "malformed",
                "rule_version": "1",
                "allowed_actions": ["calculate_dose"],
                "issued_by": "generative_model",
            },
            language="fr",
        )

        self.assertEqual(
            decision.authority_level,
            AdviceAuthorityLevel.L5_PROHIBITED,
        )
        self.assertEqual(decision.decision, AdviceDisposition.REFUSE)
        self.assertEqual(decision.issued_by, Authority.SYSTEM)
        self.assertEqual(decision.rule_id, "core.advice.fail_closed")
        self.assertFalse(decision.can_narrate_patient_action)

    def test_serialization_round_trip_preserves_authority(self):
        original = AdviceDecision(
            intent="education",
            authority_level=AdviceAuthorityLevel.L1_EDUCATION,
            decision=AdviceDisposition.ALLOW,
            rule_id="core.education.001",
            rule_version="2",
            allowed_actions=("explain_approved_data",),
            limitations=("no_diagnosis",),
            language="en",
        )

        restored = AdviceDecision.from_mapping_fail_closed(original.to_dict())

        self.assertEqual(restored, original)

    def test_contract_is_immutable(self):
        decision = AdviceDecision.fail_closed()
        with self.assertRaises(FrozenInstanceError):
            decision.intent = "mutated"  # type: ignore[misc]

    def test_action_assertion_is_fail_closed(self):
        decision = AdviceDecision.fail_closed()
        with self.assertRaises(PermissionError):
            decision.assert_action_allowed("change_treatment")


    def test_scalar_action_collection_fails_closed_instead_of_splitting_string(self):
        decision = AdviceDecision.from_mapping_fail_closed(
            {
                "intent": "education",
                "authority_level": "L1",
                "decision": "allow",
                "rule_id": "core.education.001",
                "rule_version": "1",
                "allowed_actions": "explain_approved_data",
            }
        )

        self.assertEqual(decision.rule_id, "core.advice.fail_closed")
        self.assertEqual(decision.decision, AdviceDisposition.REFUSE)

    def test_non_string_required_field_fails_closed(self):
        decision = AdviceDecision.from_mapping_fail_closed(
            {
                "intent": None,
                "authority_level": "L1",
                "decision": "allow",
                "rule_id": "core.education.001",
                "rule_version": "1",
            }
        )

        self.assertEqual(decision.rule_id, "core.advice.fail_closed")
        self.assertEqual(decision.authority_level, AdviceAuthorityLevel.L5_PROHIBITED)
