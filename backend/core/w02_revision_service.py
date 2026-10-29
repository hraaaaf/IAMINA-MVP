"""D10 option A: PREVIEW-only, server-anchored monotone revision state machine.

Two phases: reserve CAS from committed N -> pending N+1; after the browser
reports a strict-durable ciphertext write, finalize with its SHA-256 receipt.
Pending blocks ordinary restores and new writes until explicit recovery.

This server cannot independently attest IndexedDB persistence. A dishonest or
crashed client may claim an ACK. NO patient activation or production use.
"""
from __future__ import annotations

import re
import secrets

from django.db import IntegrityError, transaction

from core.models.w02_revision_anchor import W02VaultRevisionAnchor

_SLOT = re.compile(r"[A-Za-z0-9_-]{43}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_TICKET = re.compile(r"[A-Za-z0-9_-]{43}\Z")
_MAX_REVISION = 2**63 - 2


class RevisionAnchorError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _valid_slot(value: object) -> bool:
    return isinstance(value, str) and _SLOT.fullmatch(value) is not None


def _valid_revision(value: object) -> bool:
    return type(value) is int and 0 <= value <= _MAX_REVISION


def _valid_digest(value: object) -> bool:
    return isinstance(value, str) and _SHA.fullmatch(value) is not None


def _public_state(anchor):
    if anchor is None:
        return {"status": "uninitialized", "slot": None,
                "committed_revision": 0, "committed_envelope_sha256": "",
                "pending_revision": None, "pending_ticket": None}
    return {
        "status": "pending" if anchor.pending_revision is not None else "ready",
        "slot": anchor.slot,
        "committed_revision": anchor.committed_revision,
        "committed_envelope_sha256": anchor.committed_envelope_sha256,
        "pending_revision": anchor.pending_revision,
        # A pending ticket is a capability only for the authenticated owner;
        # it survives a browser reload to support explicit recovery.
        "pending_ticket": anchor.pending_ticket or None,
    }


def state_for_user(user):
    return _public_state(W02VaultRevisionAnchor.objects.filter(patient=user).first())


def reserve_revision(*, user, slot, expected_revision):
    if not _valid_slot(slot) or not _valid_revision(expected_revision):
        raise RevisionAnchorError("invalid_reservation")
    try:
        with transaction.atomic():
            anchor, _ = W02VaultRevisionAnchor.objects.get_or_create(
                patient=user,
                defaults={"slot": slot},
            )
            anchor = W02VaultRevisionAnchor.objects.select_for_update().get(pk=anchor.pk)
            if anchor.slot != slot:
                raise RevisionAnchorError("vault_scope_mismatch")
            if anchor.pending_revision is not None:
                raise RevisionAnchorError("pending_recovery_required")
            if anchor.committed_revision != expected_revision:
                raise RevisionAnchorError("stale_revision")
            if anchor.committed_revision >= _MAX_REVISION:
                raise RevisionAnchorError("revision_exhausted")
            anchor.pending_revision = expected_revision + 1
            anchor.pending_ticket = secrets.token_urlsafe(32)
            anchor.save(update_fields=["pending_revision", "pending_ticket", "updated_at"])
            return {
                "revision": anchor.pending_revision,
                "ticket": anchor.pending_ticket,
            }
    except IntegrityError as exc:
        # Cross-user slot collision or concurrent initialization, fail closed.
        raise RevisionAnchorError("revision_anchor_conflict") from exc


def finalize_revision(*, user, slot, revision, ticket, envelope_sha256):
    if (not _valid_slot(slot) or not _valid_revision(revision) or revision < 1
            or not isinstance(ticket, str) or _TICKET.fullmatch(ticket) is None
            or not _valid_digest(envelope_sha256)):
        raise RevisionAnchorError("invalid_finalize")
    with transaction.atomic():
        anchor = (W02VaultRevisionAnchor.objects.select_for_update()
                  .filter(patient=user).first())
        if anchor is None or anchor.slot != slot:
            raise RevisionAnchorError("vault_scope_mismatch")
        if anchor.pending_revision is None:
            # Idempotent only if the confirmed digest and revision match.
            if (anchor.committed_revision == revision
                    and anchor.committed_envelope_sha256 == envelope_sha256):
                return _public_state(anchor)
            raise RevisionAnchorError("no_pending_reservation")
        if anchor.pending_revision != revision or anchor.pending_ticket != ticket:
            raise RevisionAnchorError("reservation_mismatch")
        if anchor.committed_revision + 1 != revision:
            raise RevisionAnchorError("invalid_revision_chain")
        anchor.committed_revision = revision
        anchor.committed_envelope_sha256 = envelope_sha256
        anchor.pending_revision = None
        anchor.pending_ticket = ""
        anchor.save(update_fields=[
            "committed_revision", "committed_envelope_sha256",
            "pending_revision", "pending_ticket", "updated_at",
        ])
        return _public_state(anchor)
