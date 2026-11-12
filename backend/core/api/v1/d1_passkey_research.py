"""D1 research HTTP adapter — deliberately NOT registered in the IAMINA API.

Tests mount this router under an isolated URLconf to exercise real Django
sessions and CSRF. Production `diabetes.api.main` MUST NOT import it.
"""
from django.conf import settings
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, ConfigDict, SecretStr

from amina.vercel_session_auth import check_iamina_csrf
from core.d1_passkey_binding_research import (
    D1PasskeyResearchDenied,
    begin_enrollment,
    begin_verification,
    finish_enrollment,
    finish_verification,
    research_session_context,
    revoke_credential,
)

router = Router(tags=["d1-passkey-research"])


class StepUpStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: SecretStr


class CredentialRevoke(BaseModel):
    model_config = ConfigDict(extra="forbid")
    credential_id: str
    password: SecretStr


class CeremonyFinish(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ceremony_id: str
    credential: dict


class CredentialStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    credential_id: str


def _session(request):
    # Defense in depth: even a future accidental import must not enable this
    # surface unless the feature flag is explicitly set (absent in settings).
    if getattr(settings, "D1_PASSKEY_RESEARCH_ENABLED", False) is not True:
        raise HttpError(404, "Not found")
    if "HTTP_AUTHORIZATION" in request.META:
        # This *research* adapter supports cookie sessions ONLY. Never allow
        # an explicit bearer to fall back to the cookie account.
        raise HttpError(401, "Authentication required")
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or not user.is_active:
        raise HttpError(401, "Authentication required")
    if not request.COOKIES.get(settings.SESSION_COOKIE_NAME):
        raise HttpError(401, "Authentication required")
    if check_iamina_csrf(request) is not None:
        raise HttpError(403, "CSRF rejected")
    key = request.session.session_key
    if not key:
        raise HttpError(401, "Authentication required")
    return user, key


def _run(action, request, *args):
    user, key = _session(request)
    try:
        return action(user, key, *args)
    except D1PasskeyResearchDenied as exc:
        raise HttpError(403, "D1 research operation denied") from exc


@router.post("/d1-research/passkey/enroll/start")
def enroll_start(request, data: StepUpStart):
    return _run(begin_enrollment, request, data.password.get_secret_value())


@router.post("/d1-research/passkey/enroll/finish")
def enroll_finish(request, data: CeremonyFinish):
    return _run(finish_enrollment, request, data.ceremony_id, data.credential)


@router.post("/d1-research/passkey/verify/start")
def verification_start(request, data: CredentialStart):
    return _run(begin_verification, request, data.credential_id)


@router.post("/d1-research/passkey/verify/finish")
def verification_finish(request, data: CeremonyFinish):
    return _run(finish_verification, request, data.ceremony_id, data.credential)


@router.post("/d1-research/passkey/revoke")
def credential_revoke(request, data: CredentialRevoke):
    return _run(
        revoke_credential, request, data.credential_id,
        data.password.get_secret_value(),
    )


@router.post("/d1-research/passkey/session-context")
def session_context(request, data: CredentialStart):
    # Nonclinical, read-only context. Test URLconf ONLY; not mounted in main API.
    return _run(research_session_context, request, data.credential_id)
