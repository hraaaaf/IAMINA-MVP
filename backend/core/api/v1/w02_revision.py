"""D10 Option A — gated native-bearer-only anchor API, Preview only.

The existing Web BFF forwards /api/v1/... with OIDC and IAMINA bearer.
NO cookies, Firebase tokens, synthetic user ID claims, or plaintext DB bytes.
"""
import os

from ninja import Router
from ninja.errors import HttpError
from ninja.security import HttpBearer
from pydantic import BaseModel

from core.native_auth import NativeTokenError, verify_native_token
from core.w02_revision_service import (
    RevisionAnchorError, finalize_revision, reserve_revision, state_for_user,
)


def _preview_only():
    if (os.environ.get("IAMINA_W02_REVISION_ANCHOR_ENABLED") != "true"
            or os.environ.get("VERCEL_ENV") != "preview"
            or os.environ.get("IAMINA_ENV", "development").lower() == "production"):
        raise HttpError(404, "Not found")


class W02NativeOnlyBearer(HttpBearer):
    def authenticate(self, request, token):
        # The signed token is checked against the current revocation version
        # and active Django user by verify_native_token on EVERY request.
        if not token.startswith("iamina."):
            return None
        try:
            user = verify_native_token(token)
        except NativeTokenError:
            return None
        request.user = user
        return user


class ReservePayload(BaseModel):
    slot: str
    expected_revision: int


class FinalizePayload(BaseModel):
    slot: str
    revision: int
    ticket: str
    envelope_sha256: str


router = Router(tags=["w02-preview-revision"])


@router.get("/w02/vault-revision/state")
def read_vault_revision(request):
    _preview_only()
    response = state_for_user(request.auth)
    # A pending transaction is NOT permission to decrypt the last snapshot.
    return response


@router.post("/w02/vault-revision/reserve")
def reserve(request, payload: ReservePayload):
    _preview_only()
    try:
        return reserve_revision(
            user=request.auth, slot=payload.slot,
            expected_revision=payload.expected_revision,
        )
    except RevisionAnchorError as error:
        raise HttpError(409 if error.code != "invalid_reservation" else 422, error.code) from error


@router.post("/w02/vault-revision/finalize")
def finalize(request, payload: FinalizePayload):
    _preview_only()
    try:
        return finalize_revision(
            user=request.auth, slot=payload.slot, revision=payload.revision,
            ticket=payload.ticket, envelope_sha256=payload.envelope_sha256,
        )
    except RevisionAnchorError as error:
        raise HttpError(422 if error.code == "invalid_finalize" else 409, error.code) from error
