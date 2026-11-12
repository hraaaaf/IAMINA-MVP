"""D1 passkey research HTTP owner/CSRF A→B→A — isolated URLconf only.

No hosted patient, real credential, real PRF or production endpoint is tested.
"""
import json

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings

from core.models import BasePatientProfile
from passkey_research.models import D1ResearchPasskeyChallenge

RP = "iamina-review-9tskukqul-achraf-benmoussa-s-projects.vercel.app"
ROOT = "/api/v1/d1-research/passkey"
HTTP_TEST = {
    "ROOT_URLCONF": "core.tests.d1_passkey_test_urls",
    "D1_PASSKEY_RESEARCH_ENABLED": True,
    "D1_PASSKEY_RESEARCH_RP_ID": RP,
    "D1_PASSKEY_RESEARCH_ORIGIN": "https://" + RP,
}


def _csrf(client):
    response = client.get("/csrf/")
    assert response.status_code == 200
    return response.json()["csrf_token"]


def _post(client, path, payload, csrf=None, authorization=None):
    kwargs = {"data": json.dumps(payload), "content_type": "application/json"}
    if csrf is not None:
        kwargs["HTTP_X_CSRFTOKEN"] = csrf
    if authorization is not None:
        kwargs["HTTP_AUTHORIZATION"] = authorization
    return client.post(path, **kwargs)


@pytest.mark.django_db
def test_anon_and_unmounted_production_remain_denied():
    assert Client().post(ROOT + "/enroll/start", "{}",
                         content_type="application/json").status_code == 404
    with override_settings(**HTTP_TEST):
        anon = Client(enforce_csrf_checks=True)
        assert _post(anon, ROOT + "/enroll/start", {}).status_code in (401, 403)


@pytest.mark.django_db
def test_research_http_session_requires_csrf_and_denies_bearer_collision():
    with override_settings(**HTTP_TEST):
        a = User.objects.create_user(username="d1_http_owner_a")
        BasePatientProfile.objects.create(patient=a)
        client = Client(enforce_csrf_checks=True)
        client.force_login(a)
        missing = _post(client, ROOT + "/enroll/start", {})
        assert missing.status_code == 403
        csrf = _csrf(client)
        mixed = _post(
            client, ROOT + "/enroll/start", {},
            csrf=csrf, authorization="Bearer fabricated",
        )
        assert mixed.status_code in (401, 403)
        response = _post(client, ROOT + "/enroll/start", {}, csrf=csrf)
        assert response.status_code == 200, (response.status_code, response.content[:300])
        assert response.json()["options"]["rp"]["id"] == RP
        assert D1ResearchPasskeyChallenge.objects.count() == 1


@pytest.mark.django_db
def test_http_cross_account_and_session_rotation_cannot_finish_a_challenge():
    with override_settings(**HTTP_TEST):
        a = User.objects.create_user(username="d1_http_A")
        b = User.objects.create_user(username="d1_http_B")
        BasePatientProfile.objects.create(patient=a)
        BasePatientProfile.objects.create(patient=b)
        client = Client(enforce_csrf_checks=True)
        client.force_login(a)
        csrf = _csrf(client)
        start = _post(client, ROOT + "/enroll/start", {}, csrf=csrf)
        assert start.status_code == 200
        challenge_id = start.json()["ceremony_id"]
        invalid_proof = {
            "ceremony_id": challenge_id,
            "credential": {"id": "YQ", "type": "public-key",
                           "clientExtensionResults": {"prf": {"enabled": True}},
                           "response": {"attestationObject": "fake",
                                        "clientDataJSON": "fake"}},
        }
        client.force_login(b)
        csrf_b = _csrf(client)
        denied_b = _post(
            client, ROOT + "/enroll/finish", invalid_proof, csrf=csrf_b,
        )
        assert denied_b.status_code == 403
        assert D1ResearchPasskeyChallenge.objects.get(pk=challenge_id).consumed_at is None
        client.force_login(a)
        csrf_a_again = _csrf(client)
        # Even the same A cannot reuse a challenge from a prior login session.
        denied_old_session = _post(
            client, ROOT + "/enroll/finish", invalid_proof, csrf=csrf_a_again,
        )
        assert denied_old_session.status_code == 403
        assert D1ResearchPasskeyChallenge.objects.get(pk=challenge_id).consumed_at is None


@pytest.mark.django_db
def test_http_flag_default_off_fails_even_under_test_urlconf():
    with override_settings(**{**HTTP_TEST, "D1_PASSKEY_RESEARCH_ENABLED": False}):
        a = User.objects.create_user(username="d1_http_flag_off")
        BasePatientProfile.objects.create(patient=a)
        client = Client(enforce_csrf_checks=True)
        client.force_login(a)
        csrf = _csrf(client)
        assert _post(client, ROOT + "/enroll/start", {}, csrf=csrf).status_code == 404
        assert D1ResearchPasskeyChallenge.objects.count() == 0


@pytest.mark.django_db
def test_http_rejects_client_supplied_patient_identifier():
    with override_settings(**HTTP_TEST):
        a = User.objects.create_user(username="d1_http_id_spoof")
        BasePatientProfile.objects.create(patient=a)
        client = Client(enforce_csrf_checks=True)
        client.force_login(a)
        csrf = _csrf(client)
        response = _post(
            client, ROOT + "/verify/start",
            {"credential_id": "YQ", "patient_id": 999999},
            csrf=csrf,
        )
        assert response.status_code == 422
