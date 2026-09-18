from django.test import Client, TestCase, override_settings

from core.consent_notice import expected_notice_claim
from core.models import BasePatientProfile
from core.models.locale import PatientLocalePreference
from core.models.patient_module import PatientModule
from diabetes.models import DiabetesProfile


@override_settings(LLM_PROVIDER="fallback")
class HostedVercelPipelineTests(TestCase):
    def setUp(self):
        self.client = Client()
        response = self.client.post(
            "/api/v1/auth/register",
            data={
                "email": "hosted-pipeline@example.test",
                "password": "Correct-Horse-Battery-2026!",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        self.token = payload["access_token"]
        self.user_id = payload["user"]["id"]
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_auth_onboarding_consent_and_chat_pipeline(self):
        activate = self.client.post(
            "/api/v1/account/modules/diabetes/activate",
            data={},
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(activate.status_code, 200, activate.content)

        profile = self.client.patch(
            "/api/v1/profile",
            data={
                "preferred_language": "en",
                "diabetes_type": "type2",
                "treatment_type": "oral_meds",
                "unit_preference": "mg_dl",
            },
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(profile.status_code, 200, profile.content)

        locale = self.client.patch(
            "/api/v1/profile/locale",
            data={
                "ui_language": "en",
                "country_code": "MA",
                "glucose_unit": "mg/dL",
            },
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(locale.status_code, 200, locale.content)

        claim = expected_notice_claim("en")
        consent = self.client.post(
            "/api/v1/account/consent",
            data={
                "notice_version": claim.version,
                "notice_hash": claim.notice_hash,
                "locale": claim.locale,
            },
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(consent.status_code, 200, consent.content)
        self.assertTrue(consent.json()["ai_consent_given"])

        chat = self.client.post(
            "/api/v1/ai/chat",
            data={"message": "Hello IAMINA", "context_days": 14},
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(chat.status_code, 200, chat.content)
        self.assertTrue(chat.json()["reply"])

        base = BasePatientProfile.objects.get(patient_id=self.user_id)
        self.assertEqual(base.preferred_language, "en")
        self.assertTrue(base.ai_consent_given_at)
        self.assertTrue(
            PatientModule.objects.filter(
                patient=base,
                module_name="diabetes",
                is_active=True,
            ).exists()
        )
        diabetes = DiabetesProfile.objects.get(base_profile=base)
        self.assertEqual(diabetes.diabetes_type, "type2")
        self.assertEqual(diabetes.treatment_type, "oral_meds")
        preference = PatientLocalePreference.objects.get(profile=base)
        self.assertEqual(preference.ui_language, "en")
        self.assertEqual(preference.country_code, "MA")
