"""Regression gates for direct companion emergency responses."""
from django.contrib.auth.models import User
from django.test import TestCase

from companion.conversation import chat, stream_chat
from core.emergency_response import render_patient_medical_emergency_response
from core.models.locale import PatientLocalePreference
from core.models.patient import BasePatientProfile


class _ExplodingLLM:
    def complete(self, *_args, **_kwargs):  # pragma: no cover - failure is the assertion
        raise AssertionError("LLM must not run on deterministic emergency path")

    def stream(self, *_args, **_kwargs):  # pragma: no cover - failure is the assertion
        raise AssertionError("LLM must not run on deterministic emergency path")


class CompanionEmergencyAuthorityTests(TestCase):
    def _patient(self, *, confirmed_country: str | None = None):
        user = User.objects.create_user(username=f"patient-{User.objects.count()}")
        profile = BasePatientProfile.objects.create(patient=user)
        if confirmed_country:
            PatientLocalePreference.objects.create(
                profile=profile,
                country_code=confirmed_country,
                country_provenance="user_confirmed",
                response_language="fr",
                response_language_provenance="user_confirmed",
            )
        return user

    def test_confirmed_morocco_uses_versioned_registry_contact(self):
        patient = self._patient(confirmed_country="MA")
        reply = render_patient_medical_emergency_response(patient, language="fr")
        self.assertIn("150", reply)
        self.assertNotIn("le 15", reply.lower())

    def test_unconfirmed_country_fails_closed_without_any_registry_number(self):
        patient = self._patient()
        reply = render_patient_medical_emergency_response(patient, language="fr")
        for number in ("150", "190", "177"):
            self.assertNotIn(number, reply)
        self.assertIn("pas de numéro", reply.lower())

    def test_anonymous_path_is_number_free(self):
        reply = render_patient_medical_emergency_response(None, language="en")
        for number in ("150", "190", "177"):
            self.assertNotIn(number, reply)
        self.assertIn("no confirmed emergency number", reply.lower())

    def test_chat_urgent_path_uses_core_authority_and_never_calls_llm(self):
        patient = self._patient(confirmed_country="MA")
        reply = chat(
            "Je suis inconscient et j'ai du mal à respirer",
            memory=None,
            deep=None,
            llm=_ExplodingLLM(),
            language="fr",
            patient=patient,
        )
        self.assertIn("150", reply)
        self.assertNotIn("mange du sucre", reply.lower())
        self.assertNotIn("le 15", reply.lower())

    def test_stream_chat_urgent_path_uses_same_core_authority(self):
        patient = self._patient(confirmed_country="MA")
        chunks = list(
            stream_chat(
                "Je suis inconscient et j'ai du mal à respirer",
                memory=None,
                deep=None,
                llm=_ExplodingLLM(),
                language="fr",
                patient=patient,
            )
        )
        self.assertEqual(len(chunks), 1)
        self.assertIn("150", chunks[0])
        self.assertNotIn("mange du sucre", chunks[0].lower())
        self.assertNotIn("le 15", chunks[0].lower())
