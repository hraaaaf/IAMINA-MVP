from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.input_safety import ALLOW, evaluate_input_safety
from core.models import BasePatientProfile
from diabetes.models import CGMReadingRecord, DiabetesProfile, LabReport, LogEntry
from diabetes.services.clinical.engine import DiabetesEngine
from diabetes.services.clinical.whole_app_context_decision import (
    WholeAppIntent,
    classify_whole_app_context,
    resolve_whole_app_context,
)


class WholeAppContextRouterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="whole-app-user")
        base = BasePatientProfile.objects.create(
            patient=self.user,
            preferred_language="fr",
        )
        self.profile = DiabetesProfile.objects.create(
            base_profile=base,
            diabetes_type="type2",
            treatment_type="oral_meds",
            target_range_low=80,
            target_range_high=170,
            target_range_provenance="patient_declared",
        )

        now = timezone.now()
        yesterday_20 = (now - timedelta(days=1)).replace(
            hour=20,
            minute=15,
            second=0,
            microsecond=0,
        )
        yesterday_13 = yesterday_20.replace(hour=13, minute=10)
        LogEntry.objects.create(
            patient=self.user,
            logged_at=yesterday_20,
            blood_sugar=154,
            meal_type="dinner",
            meal_description="tajine poulet",
            sleep_quality="good",
            stressed="no",
        )
        LogEntry.objects.create(
            patient=self.user,
            logged_at=yesterday_13,
            blood_sugar=132,
            meal_type="lunch",
            meal_description="salade et pain",
            sleep_quality="bad",
            stressed="yes",
        )

        self.meal_episode = uuid4()
        pre_at = now - timedelta(days=2, hours=2)
        post_at = pre_at + timedelta(minutes=90)
        LogEntry.objects.create(
            patient=self.user,
            logged_at=pre_at,
            blood_sugar=110,
            glycemic_context="pre_meal",
            meal_type="lunch",
            meal_episode_id=self.meal_episode,
        )
        LogEntry.objects.create(
            patient=self.user,
            logged_at=post_at,
            blood_sugar=158,
            glycemic_context="post_meal",
            meal_type="lunch",
            meal_episode_id=self.meal_episode,
        )

        LabReport.objects.create(
            patient=self.user,
            document_type="lab_report",
            source_format="pdf",
            report_date=timezone.localdate() - timedelta(days=3),
            hba1c_pct=6.8,
            fasting_glucose_mgdl=121,
            confidence=0.94,
        )
        CGMReadingRecord.objects.create(
            patient=self.user,
            source="linx",
            recorded_at=now - timedelta(minutes=5),
            glucose_mg_dl=146,
            trend="flat",
            dedupe_key="latest-cgm-router-test",
        )

    def _resolve(self, message: str):
        resolution = resolve_whole_app_context(self.user.id, message, language="fr")
        self.assertIsNotNone(resolution, message)
        self.assertTrue(resolution.decision.rule_id.startswith("diabetes.context."))
        self.assertEqual(resolution.decision.authority_level.value, "L1")
        self.assertIn("change_treatment", resolution.decision.forbidden_actions)
        return resolution

    def test_classifier_covers_all_twelve_whole_app_gap_families(self):
        cases = {
            "Quel est mon type de diabète enregistré ?": WholeAppIntent.DIABETES_TYPE,
            "Quel traitement est enregistré dans mon profil ?": WholeAppIntent.TREATMENT,
            "Quels sont mes objectifs glycémiques enregistrés ?": WholeAppIntent.TARGETS,
            "Qu'est-ce que j'ai mangé hier ?": WholeAppIntent.MEAL_HISTORY,
            "Quelle était ma glycémie hier à 20h ?": WholeAppIntent.EXACT_GLUCOSE,
            "Comment ai-je dormi cette semaine ?": WholeAppIntent.SLEEP_HISTORY,
            "Est-ce que j'étais stressé cette semaine ?": WholeAppIntent.STRESS_HISTORY,
            "Que dit mon dernier rapport de laboratoire ?": WholeAppIntent.LATEST_LAB,
            "Quels médicaments ont été importés de mon document ?": (
                WholeAppIntent.IMPORTED_MEDICATIONS
            ),
            "Quelle est ma dernière mesure CGM exacte ?": WholeAppIntent.LATEST_CGM,
            "Quelles observations proactives sont en attente ?": WholeAppIntent.PROACTIVE_PENDING,
            "Montre-moi mes épisodes pré/post repas liés.": WholeAppIntent.PAIRED_MEALS,
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(evaluate_input_safety(message).action, ALLOW)
                self.assertEqual(classify_whole_app_context(message), expected)

    def test_profile_type_treatment_and_targets_use_persisted_profile(self):
        self.assertIn("Type 2", self._resolve("Quel est mon type de diabète enregistré ?").reply)
        self.assertIn(
            "Medicaments oraux",
            self._resolve("Quel traitement est enregistré dans mon profil ?").reply,
        )
        targets = self._resolve("Quels sont mes objectifs glycémiques enregistrés ?").reply
        self.assertIn("80–170 mg/dL", targets)
        self.assertIn("patient_declared", targets)
        self.assertIn("pas comme un objectif clinique confirmé", targets)

    def test_journal_meal_exact_glucose_sleep_and_stress_are_read_from_logs(self):
        meal = self._resolve("Qu'est-ce que j'ai mangé hier ?").reply
        self.assertIn("tajine poulet", meal)
        self.assertIn("salade et pain", meal)

        exact = self._resolve("Quelle était ma glycémie hier à 20h ?").reply
        self.assertIn("154 mg/dL", exact)
        self.assertIn("20:15", exact)

        sleep = self._resolve("Comment ai-je dormi cette semaine ?").reply
        self.assertIn("2 entrées", sleep)
        self.assertIn("1 « bon »", sleep)
        self.assertIn("1 « mauvais »", sleep)

        stress = self._resolve("Est-ce que j'étais stressé cette semaine ?").reply
        self.assertIn("2 entrées", stress)
        self.assertIn("1 « oui »", stress)
        self.assertIn("1 « non »", stress)

    def test_document_and_cgm_queries_use_persisted_structured_sources(self):
        lab = self._resolve("Que dit mon dernier rapport de laboratoire ?").reply
        self.assertIn("HbA1c 6.8 %", lab)
        self.assertIn("glycémie à jeun 121 mg/dL", lab)

        medications = self._resolve(
            "Quels médicaments ont été importés de mon document ?"
        ).reply
        self.assertIn("ne sont pas persistés comme liste structurée", medications)
        self.assertIn("sans inventer", medications)

        cgm = self._resolve("Quelle est ma dernière mesure CGM exacte ?").reply
        self.assertIn("146 mg/dL", cgm)
        self.assertIn("linx", cgm)
        self.assertIn("flat", cgm)

    @patch(
        "diabetes.services.clinical.whole_app_context_decision.preview_proactive_insights"
    )
    def test_proactive_query_is_read_only_and_uses_preview(self, preview):
        preview.return_value = SimpleNamespace(
            status="available",
            pending_count=2,
            item=SimpleNamespace(
                observation_key="context:stress",
                kind="context",
                state="persisting",
                observations=4,
                distinct_days=3,
                allowed_next_step="PREPARE_CLINICIAN_DISCUSSION",
            ),
        )

        reply = self._resolve("Quelles observations proactives sont en attente ?").reply

        preview.assert_called_once_with(patient_id=self.user.id)
        self.assertIn("2 observation(s) en attente", reply)
        self.assertIn("observation gouvernée : contexte", reply)
        self.assertNotIn("context:stress", reply)
        self.assertIn("PREPARE_CLINICIAN_DISCUSSION", reply)

    def test_paired_meal_query_uses_explicit_episode_links_only(self):
        reply = self._resolve("Montre-moi mes épisodes pré/post repas liés.").reply
        self.assertIn("1 paire(s) pré/post complète(s)", reply)
        self.assertIn("110", reply)
        self.assertIn("158", reply)
        self.assertIn("sans causalité déduite", reply)

    def test_engine_claims_whole_app_context_before_generative_narration(self):
        engine = DiabetesEngine()
        context = engine.analyze(self.user.id, language="fr", days=7)

        resolution = engine.resolve_patient_advice(
            self.user.id,
            "Quel traitement est enregistré dans mon profil ?",
            context,
            language="fr",
        )

        self.assertIsNotNone(resolution)
        self.assertEqual(
            resolution.decision.rule_id,
            "diabetes.context.profile_treatment",
        )

    def test_engine_routes_all_twelve_audit_gaps_without_generative_fallback(self):
        engine = DiabetesEngine()
        context = engine.analyze(self.user.id, language="fr", days=7)
        cases = {
            "Quel est mon type de diabète enregistré ?": "profile_diabetes_type",
            "Quel traitement est enregistré dans mon profil ?": "profile_treatment",
            "Quels sont mes objectifs glycémiques enregistrés ?": "profile_targets",
            "Qu'est-ce que j'ai mangé hier ?": "journal_meal_history",
            "Quelle était ma glycémie hier à 20h ?": "journal_exact_glucose",
            "Comment ai-je dormi cette semaine ?": "journal_sleep_history",
            "Est-ce que j'étais stressé cette semaine ?": "journal_stress_history",
            "Que dit mon dernier rapport de laboratoire ?": "document_latest_lab",
            "Quels médicaments ont été importés de mon document ?": (
                "document_imported_medications"
            ),
            "Quelle est ma dernière mesure CGM exacte ?": "cgm_latest_reading",
            "Quelles observations proactives sont en attente ?": "proactive_pending",
            "Montre-moi mes épisodes pré/post repas liés.": "paired_meal_history",
        }

        for message, suffix in cases.items():
            with self.subTest(message=message):
                resolution = engine.resolve_patient_advice(
                    self.user.id,
                    message,
                    context,
                    language="fr",
                )
                self.assertIsNotNone(resolution)
                self.assertEqual(
                    resolution.decision.rule_id,
                    f"diabetes.context.{suffix}",
                )

    def test_patient_scope_never_reads_another_users_records(self):
        other = User.objects.create_user(username="whole-app-other")
        other_base = BasePatientProfile.objects.create(
            patient=other,
            preferred_language="fr",
        )
        DiabetesProfile.objects.create(
            base_profile=other_base,
            diabetes_type="type1",
            treatment_type="insulin_pump",
        )
        CGMReadingRecord.objects.create(
            patient=other,
            source="dexcom",
            recorded_at=timezone.now(),
            glucose_mg_dl=299,
            dedupe_key="other-patient-cgm",
        )
        LabReport.objects.create(
            patient=other,
            document_type="lab_report",
            source_format="pdf",
            hba1c_pct=11.1,
            confidence=0.99,
        )

        profile_reply = self._resolve(
            "Quel est mon type de diabète enregistré ?"
        ).reply
        cgm_reply = self._resolve("Quelle est ma dernière mesure CGM exacte ?").reply
        lab_reply = self._resolve("Que dit mon dernier rapport de laboratoire ?").reply

        self.assertIn("Type 2", profile_reply)
        self.assertNotIn("Type 1", profile_reply)
        self.assertIn("146 mg/dL", cgm_reply)
        self.assertNotIn("299", cgm_reply)
        self.assertIn("6.8 %", lab_reply)
        self.assertNotIn("11.1", lab_reply)

    def test_verifier_rejects_nondeterministic_rewrite(self):
        engine = DiabetesEngine()
        resolution = self._resolve("Quel traitement est enregistré dans mon profil ?")

        verified = engine.verify_advice_reply(
            resolution,
            "Tu devrais changer ton traitement.",
        )

        self.assertEqual(verified, resolution.reply)

    def test_unrelated_message_is_not_claimed(self):
        for message in (
            "Raconte-moi une blague.",
            "Quel temps fait-il demain ?",
            "Aide-moi à rester motivé.",
            "Quel traitement devrais-je prendre ?",
        ):
            with self.subTest(message=message):
                self.assertIsNone(classify_whole_app_context(message))
