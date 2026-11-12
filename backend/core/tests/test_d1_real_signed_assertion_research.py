"""Real ECDSA P-256 signed WebAuthn assertion through isolated Django router.

All users and keys are generated synthetically in the CI process.
Unlike the orchestration tests, these tests DO NOT mock the py_webauthn
signature verifier. They are not physical Safari/Face ID/PRF evidence.
No route is mounted in production and no clinical vault is accessed.
"""
import base64
import hashlib
import json

import cbor2
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from django.contrib.auth.models import User
from django.test import Client, override_settings

from core.models import BasePatientProfile
from passkey_research.models import (
    D1ResearchPasskeyChallenge,
    D1ResearchPasskeyCredential,
)

RP = "iamina-review-9tskukqul-achraf-benmoussa-s-projects.vercel.app"
ORIGIN = "https://" + RP
PATH = "/api/v1/d1-research/passkey"
SETTINGS = {
    "ROOT_URLCONF": "core.tests.d1_passkey_test_urls",
    "D1_PASSKEY_RESEARCH_ENABLED": True,
    "D1_PASSKEY_RESEARCH_RP_ID": RP,
    "D1_PASSKEY_RESEARCH_ORIGIN": ORIGIN,
}


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def post(client, endpoint, body, csrf):
    return client.post(
        PATH + endpoint,
        data=json.dumps(body),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf,
    )


def create_credential(user):
    private = ec.generate_private_key(ec.SECP256R1())
    public_numbers = private.public_key().public_numbers()
    cose_key = cbor2.dumps({
        1: 2,  # COSE EC2
        3: -7,  # ES256
        -1: 1,  # P-256
        -2: public_numbers.x.to_bytes(32, "big"),
        -3: public_numbers.y.to_bytes(32, "big"),
    })
    cred_id = b64(b"iamina-synthetic-real-ECDSA-A")
    credential = D1ResearchPasskeyCredential.objects.create(
        patient=user,
        credential_id=cred_id,
        public_key=cose_key,
        user_handle=b"synthetic-verified-user-handle",
        sign_count=0,
        rp_id=RP,
        origin=ORIGIN,
    )
    return private, credential


def assertion(private, challenge, credential_id, *,
              origin=ORIGIN, rp_id=RP, uv=True, counter=1):
    client_data = json.dumps({
        "type": "webauthn.get",
        "challenge": challenge,
        "origin": origin,
        "crossOrigin": False,
    }, separators=(",", ":")).encode("utf-8")
    authenticator_data = (
        hashlib.sha256(rp_id.encode()).digest()
        + bytes([0x05 if uv else 0x01])
        + counter.to_bytes(4, "big")
    )
    signature = private.sign(
        authenticator_data + hashlib.sha256(client_data).digest(),
        ec.ECDSA(hashes.SHA256()),
    )
    return {
        "id": credential_id,
        "rawId": credential_id,
        "type": "public-key",
        "response": {
            "authenticatorData": b64(authenticator_data),
            "clientDataJSON": b64(client_data),
            "signature": b64(signature),
            "userHandle": None,
        },
    }


def fixture():
    owner = User.objects.create_user(
        username="d1-real-ecdsa-A",
        password="Synthetic-Only-Password-42!",
    )
    other = User.objects.create_user(
        username="d1-real-ecdsa-B",
        password="Synthetic-Only-Password-42!",
    )
    BasePatientProfile.objects.create(patient=owner)
    BasePatientProfile.objects.create(patient=other)
    private, credential = create_credential(owner)
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    csrf = client.get("/csrf/").json()["csrf_token"]
    return owner, other, private, credential, client, csrf


@pytest.mark.django_db
def test_real_ecdsa_signed_assertion_passes_and_replay_does_not():
    with override_settings(**SETTINGS):
        _owner, _other, private, credential, client, csrf = fixture()
        first = post(client, "/verify/start", {
            "credential_id": credential.credential_id,
        }, csrf)
        assert first.status_code == 200, first.content[:250]
        challenge = first.json()
        payload = {
            "ceremony_id": challenge["ceremony_id"],
            "credential": assertion(
                private, challenge["options"]["challenge"], credential.credential_id,
            ),
        }
        verified = post(client, "/verify/finish", payload, csrf)
        assert verified.status_code == 200, verified.content[:300]
        assert verified.json() == {
            "status": "ASSERTION_VERIFIED_RESEARCH_ONLY",
            "patient_ready": False,
        }
        credential.refresh_from_db()
        assert credential.sign_count == 1

        replay = post(client, "/verify/finish", payload, csrf)
        assert replay.status_code == 403
        assert D1ResearchPasskeyChallenge.objects.get(
            pk=challenge["ceremony_id"],
        ).consumed_at is not None

        second = post(client, "/verify/start", {
            "credential_id": credential.credential_id,
        }, csrf).json()
        later = post(client, "/verify/finish", {
            "ceremony_id": second["ceremony_id"],
            "credential": assertion(
                private, second["options"]["challenge"],
                credential.credential_id, counter=2,
            ),
        }, csrf)
        assert later.status_code == 200
        credential.refresh_from_db()
        assert credential.sign_count == 2


@pytest.mark.django_db
@pytest.mark.parametrize("fault", [
    "forged_signature", "foreign_origin", "foreign_rp", "missing_uv",
    "stale_counter",
])
def test_real_verifier_refuses_altered_signed_assertion(fault):
    with override_settings(**SETTINGS):
        _owner, _other, private, credential, client, csrf = fixture()
        credential.sign_count = 2 if fault == "stale_counter" else 0
        credential.save(update_fields=["sign_count"])
        start = post(client, "/verify/start", {
            "credential_id": credential.credential_id,
        }, csrf).json()
        arguments = {}
        if fault == "foreign_origin":
            arguments["origin"] = "https://foreign.invalid"
        if fault == "foreign_rp":
            arguments["rp_id"] = "foreign.invalid"
        if fault == "missing_uv":
            arguments["uv"] = False
        if fault == "stale_counter":
            arguments["counter"] = 2
        signed = assertion(
            private, start["options"]["challenge"],
            credential.credential_id, **arguments,
        )
        if fault == "forged_signature":
            raw = bytearray(base64.urlsafe_b64decode(
                signed["response"]["signature"] + "==",
            ))
            raw[-1] ^= 0x40
            signed["response"]["signature"] = b64(bytes(raw))
        denied = post(client, "/verify/finish", {
            "ceremony_id": start["ceremony_id"],
            "credential": signed,
        }, csrf)
        assert denied.status_code == 403, (fault, denied.content[:200])
        assert post(client, "/verify/finish", {
            "ceremony_id": start["ceremony_id"],
            "credential": signed,
        }, csrf).status_code == 403
        credential.refresh_from_db()
        assert credential.sign_count == (2 if fault == "stale_counter" else 0)


@pytest.mark.django_db
def test_real_signature_cannot_be_reused_under_another_django_user():
    with override_settings(**SETTINGS):
        _owner, other, private, credential, client, csrf = fixture()
        start = post(client, "/verify/start", {
            "credential_id": credential.credential_id,
        }, csrf).json()
        signed = assertion(
            private,start["options"]["challenge"],credential.credential_id,
        )
        client.force_login(other)
        csrf_other = client.get("/csrf/").json()["csrf_token"]
        assert post(client,"/verify/finish", {
            "ceremony_id":start["ceremony_id"],"credential":signed,
        },csrf_other).status_code == 403
        # A new session for original A cannot resurrect a challenge.
        original = User.objects.get(username="d1-real-ecdsa-A")
        client.force_login(original)
        csrf_original = client.get("/csrf/").json()["csrf_token"]
        assert post(client,"/verify/finish", {
            "ceremony_id":start["ceremony_id"],"credential":signed,
        },csrf_original).status_code == 403
