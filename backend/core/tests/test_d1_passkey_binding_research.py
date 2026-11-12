"""D1 research-only owner-binding contract tests (synthetic users, no patient data).

These tests replace the cryptographic library only where explicitly stated:
they prove Django ownership/nonce/session gate behaviour, NOT signature math.
Real WebAuthn signature, browser PRF, Safari FUE and integration are separate gates.
"""
import base64
from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import override_settings
from django.utils import timezone

from core.d1_passkey_binding_research import (
    D1PasskeyResearchDenied,
    begin_enrollment,
    begin_verification,
    finish_enrollment,
    finish_verification,
    revoke_credential,
)
from core.models import BasePatientProfile
from passkey_research.models import (
    D1ResearchPasskeyChallenge,
    D1ResearchPasskeyCredential,
)

RP = "iamina-review-9tskukqul-achraf-benmoussa-s-projects.vercel.app"
ORIGIN = "https://" + RP
SESSION_A = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SESSION_B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
TEST_PASSWORD = "Synthetic-D1-Only-Password-42!"
CRED_BYTES = b"synthetic-credential-A"
CRED_ID = base64.urlsafe_b64encode(CRED_BYTES).decode().rstrip("=")


@pytest.fixture
def users(db, monkeypatch):
    # Service orchestration fixtures mock only the session store; the real
    # session behaviour is tested separately with Client() below.
    monkeypatch.setattr(
        "core.d1_passkey_binding_research._assert_live_session",
        lambda user, session_key: None,
    )
    a = User.objects.create_user(username="d1_research_A", password=TEST_PASSWORD)
    b = User.objects.create_user(username="d1_research_B", password=TEST_PASSWORD)
    BasePatientProfile.objects.create(patient=a)
    BasePatientProfile.objects.create(patient=b)
    return a, b


@pytest.fixture(autouse=True)
def research_enabled():
    with override_settings(
        D1_PASSKEY_RESEARCH_ENABLED=True,
        D1_PASSKEY_RESEARCH_RP_ID=RP,
        D1_PASSKEY_RESEARCH_ORIGIN=ORIGIN,
    ):
        yield


def registration_payload(credential_id=CRED_ID):
    return {
        "id": credential_id,
        "type": "public-key",
        "authenticatorAttachment": "platform",
        "clientExtensionResults": {"prf": {"enabled": True}},
        "response": {
            "attestationObject": "synthetic-proof-only",
            "clientDataJSON": "synthetic-challenge-only",
        },
    }


def authentication_payload(credential_id=CRED_ID):
    return {
        "id": credential_id, "type": "public-key",
        "response": {
            "authenticatorData": "synthetic",
            "clientDataJSON": "synthetic",
            "signature": "synthetic",
        },
    }


@pytest.mark.django_db
def test_disabled_flag_and_insecure_origin_fail_closed(users):
    a, _ = users
    with override_settings(D1_PASSKEY_RESEARCH_ENABLED=False):
        with pytest.raises(D1PasskeyResearchDenied):
            begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    with override_settings(D1_PASSKEY_RESEARCH_ORIGIN="https://other.example"):
        with pytest.raises(D1PasskeyResearchDenied):
            begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    with override_settings(D1_PASSKEY_RESEARCH_ORIGIN="http://" + RP):
        with pytest.raises(D1PasskeyResearchDenied):
            begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    assert D1ResearchPasskeyChallenge.objects.count() == 0


@pytest.mark.django_db
def test_anonymous_inactive_and_bare_short_session_rejected(users):
    a, _ = users
    for principal, sess in ((AnonymousUser(), SESSION_A), (a, "short"), (a, "")):
        with pytest.raises(D1PasskeyResearchDenied):
            begin_enrollment(principal, sess, TEST_PASSWORD)
    a.is_active = False
    a.save(update_fields=["is_active"])
    with pytest.raises(D1PasskeyResearchDenied):
        begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    assert D1ResearchPasskeyChallenge.objects.count() == 0


@pytest.mark.django_db
def test_enroll_bound_to_original_user_session_and_revocation(users, monkeypatch):
    a, b = users
    started = begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    assert started["options"]["rp"]["id"] == RP
    challenge_id = started["ceremony_id"]
    assert D1ResearchPasskeyChallenge.objects.count() == 1
    saved = D1ResearchPasskeyChallenge.objects.get(pk=challenge_id)
    assert not hasattr(saved, "session_key")
    assert saved.session_binding != SESSION_A
    assert len(saved.session_binding) == 64

    calls = []
    def fake_verify(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            credential_id=CRED_BYTES,
            credential_public_key=b"synthetic-public-key",
            sign_count=0,
        )

    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_registration_response",
        fake_verify,
    )
    for user, session in ((b, SESSION_B), (a, SESSION_B)):
        with pytest.raises(D1PasskeyResearchDenied):
            finish_enrollment(user, session, challenge_id, registration_payload())
    assert calls == []
    assert D1ResearchPasskeyCredential.objects.count() == 0

    BasePatientProfile.objects.filter(patient=a).update(auth_token_version=1)
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, SESSION_A, challenge_id, registration_payload())
    assert calls == []
    BasePatientProfile.objects.filter(patient=a).update(auth_token_version=0)

    assert finish_enrollment(
        a, SESSION_A, challenge_id, registration_payload(),
    )["status"] == "BOUND_RESEARCH_ONLY"
    assert D1ResearchPasskeyCredential.objects.get().patient_id == a.pk
    assert calls[0]["expected_origin"] == ORIGIN
    assert calls[0]["expected_rp_id"] == RP
    assert calls[0]["require_user_verification"] is True

    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, SESSION_A, challenge_id, registration_payload())
    assert len(calls) == 1


@pytest.mark.django_db
def test_negative_registration_burns_nonce_even_when_verifier_rejects(users, monkeypatch):
    a, _ = users
    started = begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    count = {"n": 0}

    def reject(**kwargs):
        count["n"] += 1
        raise ValueError("bad signature")

    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_registration_response",
        reject,
    )
    for _ in range(2):
        with pytest.raises(D1PasskeyResearchDenied):
            finish_enrollment(a, SESSION_A, started["ceremony_id"], registration_payload())
    assert count["n"] == 1
    assert D1ResearchPasskeyCredential.objects.count() == 0


@pytest.mark.django_db
def test_expired_nonce_does_not_reach_verifier(users, monkeypatch):
    a, _ = users
    challenge_id = begin_enrollment(a, SESSION_A, TEST_PASSWORD)["ceremony_id"]
    D1ResearchPasskeyChallenge.objects.filter(pk=challenge_id).update(
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_registration_response",
        lambda **kwargs: pytest.fail("expired challenge entered verifier"),
    )
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, SESSION_A, challenge_id, registration_payload())


@pytest.mark.django_db
def test_untrusted_prf_client_claim_never_bypasses_server_signature(users, monkeypatch):
    a, _ = users
    began = begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    p = registration_payload()
    p["clientExtensionResults"]["prf"]["enabled"] = False
    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_registration_response",
        lambda **kw: pytest.fail("PRF disabled entered verifier"),
    )
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, SESSION_A, began["ceremony_id"], p)
    assert D1ResearchPasskeyCredential.objects.count() == 0


@pytest.mark.django_db
def test_verification_cross_user_and_wrong_credential_fail_closed(users, monkeypatch):
    a, b = users
    binding = D1ResearchPasskeyCredential.objects.create(
        patient=a,
        credential_id=CRED_ID,
        public_key=b"synthetic-public-key",
        user_handle=b"synthetic-handle",
        rp_id=RP,
        origin=ORIGIN,
    )
    with pytest.raises(D1PasskeyResearchDenied):
        begin_verification(b, SESSION_B, CRED_ID)
    assert D1ResearchPasskeyChallenge.objects.count() == 0

    started = begin_verification(a, SESSION_A, CRED_ID)
    assert started["options"]["rpId"] == RP
    called = []
    def fake_verify(**kw):
        called.append(kw)
        return SimpleNamespace(new_sign_count=1)
    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_authentication_response",
        fake_verify,
    )
    for principal, sess in ((b, SESSION_B), (a, SESSION_B)):
        with pytest.raises(D1PasskeyResearchDenied):
            finish_verification(principal, sess, started["ceremony_id"], authentication_payload())
    assert called == []

    bad = authentication_payload(credential_id="d3Jvbmc")
    with pytest.raises(D1PasskeyResearchDenied):
        finish_verification(a, SESSION_A, started["ceremony_id"], bad)
    # Wrong credential consumes the nonce; cannot substitute a correct one after.
    with pytest.raises(D1PasskeyResearchDenied):
        finish_verification(a, SESSION_A, started["ceremony_id"], authentication_payload())
    assert called == []
    binding.refresh_from_db()
    assert binding.sign_count == 0

    second = begin_verification(a, SESSION_A, CRED_ID)
    assert finish_verification(
        a, SESSION_A, second["ceremony_id"], authentication_payload(),
    )["status"] == "ASSERTION_VERIFIED_RESEARCH_ONLY"
    binding.refresh_from_db()
    assert binding.sign_count == 1
    assert called[0]["require_user_verification"] is True
    assert called[0]["expected_origin"] == ORIGIN
    assert called[0]["expected_rp_id"] == RP


@pytest.mark.django_db
def test_nonadvancing_signature_counter_is_denied(users, monkeypatch):
    a, _ = users
    binding = D1ResearchPasskeyCredential.objects.create(
        patient=a, credential_id=CRED_ID,
        public_key=b"synthetic-public-key", user_handle=b"synthetic-handle",
        rp_id=RP, origin=ORIGIN, sign_count=5,
    )
    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_authentication_response",
        lambda **kw: SimpleNamespace(new_sign_count=5),
    )
    started = begin_verification(a, SESSION_A, binding.credential_id)
    with pytest.raises(D1PasskeyResearchDenied):
        finish_verification(a, SESSION_A, started["ceremony_id"], authentication_payload())
    binding.refresh_from_db()
    assert binding.sign_count == 5


@pytest.mark.django_db
def test_revoke_credential_denies_any_new_verification(users):
    a, _ = users
    binding = D1ResearchPasskeyCredential.objects.create(
        patient=a, credential_id=CRED_ID,
        public_key=b"synthetic-public-key", user_handle=b"synthetic-handle",
        rp_id=RP, origin=ORIGIN, revoked_at=timezone.now(),
    )
    with pytest.raises(D1PasskeyResearchDenied):
        begin_verification(a, SESSION_A, binding.credential_id)


@pytest.mark.django_db
def test_no_d1_passkey_http_route_exposed(users):
    from django.test import Client
    a, _ = users
    client = Client(enforce_csrf_checks=True)
    client.force_login(a)
    # The service remains deliberately unmounted: no Web API write surface.
    response = client.post(
        "/api/v1/account/passkey-research/enroll",
        data="{}", content_type="application/json",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_same_credential_cannot_be_rebound_to_user_b(users, monkeypatch):
    a, b = users
    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_registration_response",
        lambda **kwargs: SimpleNamespace(
            credential_id=CRED_BYTES,
            credential_public_key=b"synthetic-public-key",
            sign_count=0,
        ),
    )
    a_ceremony = begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    finish_enrollment(a, SESSION_A, a_ceremony["ceremony_id"], registration_payload())
    b_ceremony = begin_enrollment(b, SESSION_B, TEST_PASSWORD)
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(b, SESSION_B, b_ceremony["ceremony_id"], registration_payload())
    assert D1ResearchPasskeyCredential.objects.count() == 1
    assert D1ResearchPasskeyCredential.objects.get().patient_id == a.pk


@pytest.mark.django_db
def test_noncanonical_alias_id_and_malformed_challenge_refused(users, monkeypatch):
    a, _ = users
    began = begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, SESSION_A, "not-a-uuid", registration_payload())
    assert D1ResearchPasskeyChallenge.objects.get(pk=began["ceremony_id"]).consumed_at is None
    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_registration_response",
        lambda **kwargs: pytest.fail("noncanonical credential reached verifier"),
    )
    payload = registration_payload()
    payload["id"] = CRED_ID + "="
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, SESSION_A, began["ceremony_id"], payload)
    assert D1ResearchPasskeyChallenge.objects.get(pk=began["ceremony_id"]).consumed_at is not None


@pytest.mark.django_db
def test_logout_during_signature_verification_rejects_late_result(users, monkeypatch):
    a, _ = users
    began = begin_enrollment(a, SESSION_A, TEST_PASSWORD)

    def revoked_during_verification(**kwargs):
        BasePatientProfile.objects.filter(patient=a).update(auth_token_version=2)
        return SimpleNamespace(
            credential_id=CRED_BYTES, credential_public_key=b"synthetic-public-key",
            sign_count=0,
        )

    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_registration_response",
        revoked_during_verification,
    )
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, SESSION_A, began["ceremony_id"], registration_payload())
    assert D1ResearchPasskeyCredential.objects.count() == 0


@pytest.mark.django_db
def test_invalid_extension_shape_is_refused_without_server_error(users):
    a, _ = users
    began = begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    payload = registration_payload()
    payload["clientExtensionResults"] = None
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, SESSION_A, began["ceremony_id"], payload)


@pytest.mark.django_db
def test_stepup_wrong_password_or_unusable_account_rejects_before_challenge(users):
    a, _ = users
    with pytest.raises(D1PasskeyResearchDenied):
        begin_enrollment(a, SESSION_A, "wrong-password")
    assert D1ResearchPasskeyChallenge.objects.count() == 0
    a.set_unusable_password()
    a.save(update_fields=["password"])
    with pytest.raises(D1PasskeyResearchDenied):
        begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    assert D1ResearchPasskeyChallenge.objects.count() == 0


@pytest.mark.django_db
def test_stepup_bruteforce_limit_rejects_even_correct_password_after_limit(users):
    a, _ = users
    for _ in range(10):
        with pytest.raises(D1PasskeyResearchDenied):
            begin_enrollment(a, SESSION_A, "incorrect")
    with pytest.raises(D1PasskeyResearchDenied):
        begin_enrollment(a, SESSION_A, TEST_PASSWORD)
    assert D1ResearchPasskeyChallenge.objects.count() == 0


@pytest.mark.django_db
def test_owner_only_revoke_requires_stepup_and_rejects_revoked_credential(users):
    a, b = users
    binding = D1ResearchPasskeyCredential.objects.create(
        patient=a, credential_id=CRED_ID, public_key=b"synthetic-pk",
        user_handle=b"handle", rp_id=RP, origin=ORIGIN,
    )
    with pytest.raises(D1PasskeyResearchDenied):
        revoke_credential(b, SESSION_B, CRED_ID, TEST_PASSWORD)
    with pytest.raises(D1PasskeyResearchDenied):
        revoke_credential(a, SESSION_A, CRED_ID, "incorrect")
    binding.refresh_from_db()
    assert binding.revoked_at is None
    assert revoke_credential(a, SESSION_A, CRED_ID, TEST_PASSWORD)["patient_ready"] is False
    binding.refresh_from_db()
    assert binding.revoked_at is not None
    with pytest.raises(D1PasskeyResearchDenied):
        begin_verification(a, SESSION_A, CRED_ID)
    with pytest.raises(D1PasskeyResearchDenied):
        revoke_credential(a, SESSION_A, CRED_ID, TEST_PASSWORD)


@pytest.mark.django_db
def test_real_django_logout_during_signature_rejects_late_enrollment(monkeypatch):
    from django.test import Client
    a = User.objects.create_user(username="d1_live_logout", password=TEST_PASSWORD)
    BasePatientProfile.objects.create(patient=a)
    client = Client()
    client.force_login(a)
    key = client.session.session_key
    ceremony_id = begin_enrollment(a, key, TEST_PASSWORD)["ceremony_id"]
    def logout_mid_verify(**kwargs):
        client.logout()  # Invalidate session without touching auth_token_version.
        return SimpleNamespace(credential_id=CRED_BYTES, credential_public_key=b"pk", sign_count=0)
    monkeypatch.setattr(
        "core.d1_passkey_binding_research.verify_registration_response",
        logout_mid_verify,
    )
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, key, ceremony_id, registration_payload())
    assert D1ResearchPasskeyCredential.objects.count() == 0


@pytest.mark.django_db
def test_real_django_session_destroyed_rejects_old_ceremony():
    from django.test import Client
    a = User.objects.create_user(username="d1_live_old", password=TEST_PASSWORD)
    BasePatientProfile.objects.create(patient=a)
    client = Client()
    client.force_login(a)
    key = client.session.session_key
    cid = begin_enrollment(a, key, TEST_PASSWORD)["ceremony_id"]
    client.logout()
    with pytest.raises(D1PasskeyResearchDenied):
        begin_enrollment(a, key, TEST_PASSWORD)
    with pytest.raises(D1PasskeyResearchDenied):
        finish_enrollment(a, key, cid, registration_payload())
