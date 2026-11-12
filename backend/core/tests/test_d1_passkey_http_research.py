"""D1 passkey research HTTP owner/CSRF A→B→A — isolated URLconf only.

No hosted patient, real credential, real PRF or production endpoint is tested.
"""
import base64
import json

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.utils import timezone

from core.models import BasePatientProfile
from passkey_research.models import D1ResearchPasskeyChallenge, D1ResearchPasskeyCredential

RP = "iamina-review-9tskukqul-achraf-benmoussa-s-projects.vercel.app"
ROOT = "/api/v1/d1-research/passkey"
TEST_PASSWORD = "Synthetic-D1-Only-Password-42!"
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
        assert _post(anon, ROOT + "/enroll/start", {"password": TEST_PASSWORD}).status_code in (401, 403)


@pytest.mark.django_db
def test_research_http_session_requires_csrf_and_denies_bearer_collision():
    with override_settings(**HTTP_TEST):
        a = User.objects.create_user(username="d1_http_owner_a", password=TEST_PASSWORD)
        BasePatientProfile.objects.create(patient=a)
        client = Client(enforce_csrf_checks=True)
        client.force_login(a)
        missing = _post(client, ROOT + "/enroll/start", {"password": TEST_PASSWORD})
        assert missing.status_code == 403
        csrf = _csrf(client)
        mixed = _post(
            client, ROOT + "/enroll/start", {},
            csrf=csrf, authorization="Bearer fabricated",
        )
        assert mixed.status_code in (401, 403)
        response = _post(client, ROOT + "/enroll/start", {"password": TEST_PASSWORD}, csrf=csrf)
        assert response.status_code == 200, (response.status_code, response.content[:300])
        assert response.json()["options"]["rp"]["id"] == RP
        assert D1ResearchPasskeyChallenge.objects.count() == 1


@pytest.mark.django_db
def test_http_cross_account_and_session_rotation_cannot_finish_a_challenge():
    with override_settings(**HTTP_TEST):
        a = User.objects.create_user(username="d1_http_A", password=TEST_PASSWORD)
        b = User.objects.create_user(username="d1_http_B", password=TEST_PASSWORD)
        BasePatientProfile.objects.create(patient=a)
        BasePatientProfile.objects.create(patient=b)
        client = Client(enforce_csrf_checks=True)
        client.force_login(a)
        csrf = _csrf(client)
        start = _post(client, ROOT + "/enroll/start", {"password": TEST_PASSWORD}, csrf=csrf)
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
        a = User.objects.create_user(username="d1_http_flag_off", password=TEST_PASSWORD)
        BasePatientProfile.objects.create(patient=a)
        client = Client(enforce_csrf_checks=True)
        client.force_login(a)
        csrf = _csrf(client)
        assert _post(client, ROOT + "/enroll/start", {"password": TEST_PASSWORD}, csrf=csrf).status_code == 404
        assert D1ResearchPasskeyChallenge.objects.count() == 0


@pytest.mark.django_db
def test_http_rejects_client_supplied_patient_identifier():
    with override_settings(**HTTP_TEST):
        a = User.objects.create_user(username="d1_http_id_spoof", password=TEST_PASSWORD)
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


@pytest.mark.django_db
def test_http_step_up_missing_and_wrong_password_does_not_enroll():
    with override_settings(**HTTP_TEST):
        a = User.objects.create_user(username="d1_http_stepup", password=TEST_PASSWORD)
        BasePatientProfile.objects.create(patient=a)
        client = Client(enforce_csrf_checks=True)
        client.force_login(a)
        csrf = _csrf(client)
        assert _post(client, ROOT + "/enroll/start", {}, csrf=csrf).status_code == 422
        bad = _post(client, ROOT + "/enroll/start", {"password": "incorrect"}, csrf=csrf)
        assert bad.status_code == 403
        assert D1ResearchPasskeyChallenge.objects.count() == 0
        good = _post(client, ROOT + "/enroll/start", {"password": TEST_PASSWORD}, csrf=csrf)
        assert good.status_code == 200


@pytest.mark.django_db
def test_http_credential_revoke_requires_owner_and_password():
    with override_settings(**HTTP_TEST):
        a = User.objects.create_user(username="d1_http_revoker_a", password=TEST_PASSWORD)
        b = User.objects.create_user(username="d1_http_revoker_b", password=TEST_PASSWORD)
        BasePatientProfile.objects.create(patient=a)
        BasePatientProfile.objects.create(patient=b)
        cid = base64.urlsafe_b64encode(b"synthetic-credential").decode().rstrip("=")
        binding = D1ResearchPasskeyCredential.objects.create(
            patient=a, credential_id=cid, public_key=b"pk", user_handle=b"handle",
            rp_id=RP, origin="https://" + RP,
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(b)
        csrf = _csrf(client)
        assert _post(client, ROOT + "/revoke",
                     {"credential_id": cid, "password": TEST_PASSWORD}, csrf=csrf).status_code == 403
        client.force_login(a)
        csrf = _csrf(client)
        assert _post(client, ROOT + "/revoke",
                     {"credential_id": cid, "password": "incorrect"}, csrf=csrf).status_code == 403
        response = _post(client, ROOT + "/revoke",
                         {"credential_id": cid, "password": TEST_PASSWORD}, csrf=csrf)
        assert response.status_code == 200
        assert response.json()["patient_ready"] is False
        binding.refresh_from_db()
        assert binding.revoked_at is not None


@pytest.mark.django_db
def test_d1_session_context_only_returns_server_owned_credential_scope():
    with override_settings(**HTTP_TEST):
        a = User.objects.create_user(
            username="d1_context_A", password=TEST_PASSWORD,
        )
        b = User.objects.create_user(
            username="d1_context_B", password=TEST_PASSWORD,
        )
        BasePatientProfile.objects.create(patient=a)
        BasePatientProfile.objects.create(patient=b)
        credential = base64.urlsafe_b64encode(b"session-fixture-credential-A").decode().rstrip("=")
        D1ResearchPasskeyCredential.objects.create(
            patient=a, credential_id=credential, public_key=b"synthetic-pub-key",
            user_handle=b"synthetic-user-handle", rp_id=RP,
            origin="https://" + RP,
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(a)
        missing_csrf = _post(client, ROOT + "/session-context", {"credential_id": credential})
        assert missing_csrf.status_code == 403
        csrf_a = _csrf(client)
        a_scope = _post(client, ROOT + "/session-context",
                        {"credential_id": credential}, csrf=csrf_a)
        assert a_scope.status_code == 200, a_scope.content[:250]
        snapshot = a_scope.json()
        assert snapshot == {
            "authenticated": True,
            "patientReady": False,
            "origin": "https://" + RP,
            "accountId": str(a.pk),
            "vaultOwner": f"amina_vault_v1_native_{a.pk}",
            "credentialId": credential,
            "epoch": 0,
            "sessionStamp": snapshot["sessionStamp"],
        }
        assert len(snapshot["sessionStamp"]) == 64
        assert snapshot["sessionStamp"] != client.session.session_key
        assert "password" not in str(snapshot).lower()
        assert "dek" not in str(snapshot).lower()

        bearer = _post(client, ROOT + "/session-context",
                       {"credential_id": credential}, csrf=csrf_a,
                       authorization="Bearer wrong")
        assert bearer.status_code in (401, 403)

        client.force_login(b)
        csrf_b = _csrf(client)
        foreign = _post(client, ROOT + "/session-context",
                        {"credential_id": credential}, csrf=csrf_b)
        assert foreign.status_code == 403

        client.force_login(a)
        csrf_a_again = _csrf(client)
        a_again = _post(client, ROOT + "/session-context",
                        {"credential_id": credential}, csrf=csrf_a_again)
        assert a_again.status_code == 200
        assert a_again.json()["sessionStamp"] != snapshot["sessionStamp"]

        binding = D1ResearchPasskeyCredential.objects.get(credential_id=credential)
        binding.revoked_at = timezone.now()
        binding.save(update_fields=["revoked_at"])
        rejected = _post(client, ROOT + "/session-context",
                         {"credential_id": credential}, csrf=csrf_a_again)
        assert rejected.status_code == 403


@pytest.mark.django_db
def test_d1_session_context_fails_closed_outside_test_urlconf():
    client = Client(enforce_csrf_checks=True)
    response = _post(
        client,
        "/api/v1/d1-research/passkey/session-context",
        {"credential_id": "Y3JlZGVudGlhbC1B"},
    )
    assert response.status_code == 404
