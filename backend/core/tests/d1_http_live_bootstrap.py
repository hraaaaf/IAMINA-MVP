"""Provision synthetic Django users, WebAuthn public key and sessions for live localhost CI.

Inputs/outputs are runner-temp JSON (chmod 0600). Never print cookies,
private JWK, CSRF token, passwords or patient data. This script is NOT in an
installed Django command or production routing configuration.
"""
import base64
import json
import os
from pathlib import Path

import cbor2
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.tests.d1_http_live_settings")
django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.test import Client  # noqa: E402

from core.models import BasePatientProfile  # noqa: E402
from passkey_research.models import D1ResearchPasskeyCredential  # noqa: E402


def decode(value):
    return base64.urlsafe_b64decode(value + "=" * ((-len(value)) % 4))


def session_for(user):
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    csrf = client.get("/csrf/")
    if csrf.status_code != 200:
        raise RuntimeError("D1 HTTP synthetic CSRF initialization failed")
    cookies = "; ".join(
        name + "=" + morsel.value for name, morsel in client.cookies.items()
    )
    return {"cookie": cookies, "csrf": csrf.json()["csrf_token"]}


def main():
    keyfile = json.loads(Path(os.environ["D1_KEYS_JSON"]).read_text())
    jwk = keyfile["key"]
    numbers = {
        1: 2, 3: -7, -1: 1,
        -2: decode(jwk["x"]), -3: decode(jwk["y"]),
    }
    user_a = User.objects.create_user("d1_http_real_A", password="synthetic-a-only")
    user_b = User.objects.create_user("d1_http_real_B", password="synthetic-b-only")
    BasePatientProfile.objects.create(patient=user_a)
    BasePatientProfile.objects.create(patient=user_b)
    D1ResearchPasskeyCredential.objects.create(
        patient=user_a,
        credential_id=keyfile["credential_id"],
        public_key=cbor2.dumps(numbers),
        user_handle=b"d1-live-http-userhandle-a",
        sign_count=0,
        rp_id=keyfile["origin"].removeprefix("https://"),
        origin=keyfile["origin"],
    )
    output = {
        "origin": keyfile["origin"],
        "credential_id": keyfile["credential_id"],
        "a": session_for(user_a),
        "b": session_for(user_b),
        "a_again": session_for(user_a),
    }
    target = Path(os.environ["D1_SESSIONS_JSON"])
    with target.open("x") as sink:
        os.chmod(target, 0o600)
        json.dump(output, sink)
    print("D1 synthetic account and sessions provisioned (no secrets displayed).")


if __name__ == "__main__":
    main()
