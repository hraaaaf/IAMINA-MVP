"""W02/D10 Option A contract — PostgreSQL-only synthetic backend tests."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.db import close_old_connections, connections

from core.models.w02_revision_anchor import W02VaultRevisionAnchor
from core.native_auth import issue_native_token, revoke_native_tokens
from core.w02_revision_service import (
    RevisionAnchorError, finalize_revision, reserve_revision, state_for_user,
)

SLOT_A = "a" * 43
SLOT_B = "b" * 43
HASH_A = "e" * 64
HASH_B = "f" * 64
PREVIEW = {"VERCEL_ENV": "preview", "IAMINA_ENV": "preview",
           "IAMINA_W02_REVISION_ANCHOR_ENABLED": "true"}
API = "/api/v1/w02/vault-revision"


def _identity(name):
    user = User.objects.create_user(username=name, password="synthetic-only")
    return user, issue_native_token(user)


def _client(token):
    return Client(HTTP_AUTHORIZATION="Bearer " + token)


@pytest.mark.django_db
def test_disabled_by_default_and_no_production_activation():
    _, bearer = _identity("off")
    client = _client(bearer)
    assert client.get(API + "/state").status_code == 404
    with patch.dict(os.environ, {**PREVIEW, "VERCEL_ENV": "production"}):
        assert client.get(API + "/state").status_code == 404
    with patch.dict(os.environ, {**PREVIEW, "IAMINA_ENV": "production"}):
        assert client.get(API + "/state").status_code == 404
    assert W02VaultRevisionAnchor.objects.count() == 0


@pytest.mark.django_db
def test_native_bearer_required_and_firebase_or_session_do_not_grant_access():
    user, bearer = _identity("onlynative")
    with patch.dict(os.environ, PREVIEW):
        assert Client().get(API + "/state").status_code in (401, 403)
        assert Client(HTTP_AUTHORIZATION="Bearer firebase-example").get(
            API + "/state").status_code in (401, 403)
        assert _client(bearer).get(API + "/state").status_code == 200
        revoke_native_tokens(user)
        assert _client(bearer).get(API + "/state").status_code in (401, 403)


@pytest.mark.django_db
def test_reserve_finalize_cas_idempotence_and_rollback_denial():
    _, bearer = _identity("owner_a")
    client = _client(bearer)
    with patch.dict(os.environ, PREVIEW):
        state = client.get(API + "/state")
        assert state.status_code == 200
        assert state.json()["status"] == "uninitialized"
        assert state.json()["vault_id"].startswith("amina_vault_v1_native_")
        reserve = client.post(API + "/reserve", data={"slot": SLOT_A, "expected_revision": 0},
                              content_type="application/json")
        assert reserve.status_code == 200, reserve.content
        receipt = reserve.json()
        assert receipt["revision"] == 1
        assert receipt["vault_id"] == state.json()["vault_id"]
        assert len(receipt["ticket"]) == 43
        assert client.get(API + "/state").json()["status"] == "pending"
        # Never expose last committed snapshot while pending.
        assert client.post(API + "/reserve", data={"slot": SLOT_A, "expected_revision": 0},
                           content_type="application/json").status_code == 409
        payload = {"slot": SLOT_A, "revision": 1,
                   "ticket": receipt["ticket"], "envelope_sha256": HASH_A}
        assert client.post(API + "/finalize", data=payload,
                           content_type="application/json").status_code == 200
        assert client.post(API + "/finalize", data=payload,
                           content_type="application/json").status_code == 200
        ready = client.get(API + "/state").json()
        assert ready["status"] == "ready"
        assert ready["committed_revision"] == 1
        assert ready["committed_envelope_sha256"] == HASH_A
        assert ready["pending_ticket"] is None
        assert client.post(API + "/reserve", data={"slot": SLOT_A, "expected_revision": 0},
                           content_type="application/json").status_code == 409
        assert client.post(API + "/finalize",
                           data={**payload, "envelope_sha256": HASH_B},
                           content_type="application/json").status_code == 409
        assert client.post(API + "/reserve", data={"slot": SLOT_A, "expected_revision": 1},
                           content_type="application/json").json()["revision"] == 2


@pytest.mark.django_db
def test_pending_crash_recovery_requires_same_ticket_and_durable_confirmation():
    owner, _ = _identity("recovery")
    first = reserve_revision(user=owner, slot=SLOT_A, expected_revision=0)
    assert state_for_user(owner)["status"] == "pending"
    assert state_for_user(owner)["pending_ticket"] == first["ticket"]
    with pytest.raises(RevisionAnchorError, match="pending_recovery_required"):
        reserve_revision(user=owner, slot=SLOT_A, expected_revision=0)
    with pytest.raises(RevisionAnchorError, match="reservation_mismatch"):
        finalize_revision(user=owner, slot=SLOT_A, revision=1,
                          ticket="x" * 43, envelope_sha256=HASH_A)
    assert state_for_user(owner)["committed_revision"] == 0
    final = finalize_revision(user=owner, slot=SLOT_A, revision=1,
                              ticket=first["ticket"], envelope_sha256=HASH_A)
    assert final["status"] == "ready"
    assert final["committed_revision"] == 1


@pytest.mark.django_db
def test_a_b_isolation_unknown_slot_conflict_and_delete_cascade():
    owner_a, _ = _identity("scope_A")
    owner_b, _ = _identity("scope_B")
    reserve_revision(user=owner_a, slot=SLOT_A, expected_revision=0)
    assert state_for_user(owner_b)["status"] == "uninitialized"
    with pytest.raises(RevisionAnchorError, match="revision_anchor_conflict"):
        reserve_revision(user=owner_b, slot=SLOT_A, expected_revision=0)
    assert state_for_user(owner_b)["status"] == "uninitialized"
    reserve_revision(user=owner_b, slot=SLOT_B, expected_revision=0)
    with pytest.raises(RevisionAnchorError, match="vault_scope_mismatch"):
        reserve_revision(user=owner_a, slot=SLOT_B, expected_revision=0)
    owner_a.delete()
    assert W02VaultRevisionAnchor.objects.count() == 1
    assert W02VaultRevisionAnchor.objects.get().patient_id == owner_b.pk


@pytest.mark.django_db
@pytest.mark.parametrize("slot,rev", [("foo", 0), (SLOT_A, -1), (SLOT_A, True),
                                      (SLOT_A, 2**63)])
def test_reject_malformed_scope_and_revisions_without_write(slot, rev):
    owner, _ = _identity("invalid" + str(rev).replace("-", "_"))
    with pytest.raises(RevisionAnchorError):
        reserve_revision(user=owner, slot=slot, expected_revision=rev)
    assert W02VaultRevisionAnchor.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_postgres_two_concurrent_reserves_exactly_one_wins():
    from django.db import connection
    if connection.vendor != "postgresql":
        pytest.skip("requires real Postgres row locking")
    owner, _ = _identity("concurrent")
    barrier = Barrier(2)
    def attempt():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            return reserve_revision(user=owner, slot=SLOT_A, expected_revision=0)
        except RevisionAnchorError as exc:
            return exc.code
        finally:
            # Postgres TransactionTestCase needs zero worker sessions before
            # teardown DROP DATABASE. close_old_connections alone preserves
            # healthy persistent connections (CONN_MAX_AGE=600).
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: attempt(), range(2)))
    assert sum(isinstance(x, dict) for x in outcomes) == 1, outcomes
    assert sum(isinstance(x, str) for x in outcomes) == 1, outcomes
    assert W02VaultRevisionAnchor.objects.get(patient=owner).pending_revision == 1
