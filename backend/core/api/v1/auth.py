"""Authentication and Firebase-to-Django migration endpoints.

Django ``User`` is the authoritative identity. Firebase is accepted only as a
temporary migration credential. Native registration and login do not depend on
Firebase and never synthesize clinical or demographic facts.
"""

import logging
import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, ConfigDict, field_validator

from core.auth_migration import (
    FirebaseIdentityConflict,
    FirebaseMigrationError,
    migrate_new_firebase_identity,
    verify_firebase_token,
)
from core.models import BasePatientProfile
from core.native_auth import (
    NATIVE_SESSION_ISSUED_AT_KEY,
    NativeTokenError,
    issue_native_token,
    native_token_max_age_seconds,
    revoke_native_tokens,
    verify_native_token,
)
from core.observability import EVT_SESSION_START, track

logger = logging.getLogger(__name__)

router = Router(tags=["auth"])


class FirebaseAuthRequest(BaseModel):
    id_token: str


class NativeRegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized or "@" not in normalized or len(normalized) > 254:
            raise ValueError("invalid_email")
        return normalized


class NativeLoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class SetPasswordRequest(BaseModel):
    new_password: str
    current_password: str | None = None


class PasswordResetRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class PasswordResetConfirmRequest(BaseModel):
    uid: str
    token: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    user: UserResponse
    message: str
    access_token: str
    token_type: str = "Bearer"


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "created_at": user.date_joined.isoformat(),
    }


def _auth_response(user: User, message: str) -> dict:
    return {
        "user": _serialize_user(user),
        "message": message,
        "access_token": issue_native_token(user),
        "token_type": "Bearer",
    }


def _require_authenticated(request) -> User:
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    return request.user


def _open_session(request, user: User, *, method: str) -> None:
    # F08 candidate: a native login issues TWO authorities (signed bearer and
    # Django session cookie). The cookie must never outlive the bearer merely
    # because Django's global SESSION_COOKIE_AGE is 14 days. Use an absolute
    # datetime, not a sliding integer TTL: unrelated session writes must not
    # extend it, and a shorter configured bearer TTL shortens it as well.
    # Compute policy before login so invalid settings cannot create a session.
    issued_at = timezone.now()
    absolute_expiry = issued_at + timedelta(seconds=native_token_max_age_seconds())
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    # An independently enforced issuance marker also rejects 14-day cookies
    # minted by older deployments, or cookies from an unbounded auth flow.
    request.session[NATIVE_SESSION_ISSUED_AT_KEY] = issued_at.isoformat()
    request.session.set_expiry(absolute_expiry)
    track(EVT_SESSION_START, patient_id=user.id, props={"method": method})


def _native_registration_allowed_in_environment() -> bool:
    """Deny native account creation on hosted Preview unless explicitly opted in.

    VERCEL_ENV is the hosting source of truth; IAMINA_ENV also protects
    preview-like local/rehearsal runtimes. Production remains unchanged.
    """
    preview = (
        os.environ.get("VERCEL_ENV", "").strip().lower() == "preview"
        or os.environ.get("IAMINA_ENV", "").strip().lower() == "preview"
    )
    return not preview or os.environ.get("IAMINA_PREVIEW_ALLOW_REGISTRATION") == "true"


@router.post("/auth/register", response=AuthResponse)
@transaction.atomic
def register_native(request, data: NativeRegisterRequest):
    """Create a sovereign Django identity without fabricating patient facts."""
    if not _native_registration_allowed_in_environment():
        raise HttpError(403, "Registration disabled in synthetic Preview")
    if User.objects.filter(email__iexact=data.email).exists():
        raise HttpError(409, "Account already exists")

    candidate = User(username=data.email, email=data.email)
    try:
        validate_password(data.password, user=candidate)
    except ValidationError as exc:
        raise HttpError(400, "Password does not meet security requirements") from exc

    user = User.objects.create_user(
        username=data.email,
        email=data.email,
        password=data.password,
        first_name=data.first_name.strip()[:150],
        last_name=data.last_name.strip()[:150],
    )
    BasePatientProfile.objects.create(patient=user)
    _open_session(request, user, method="django_password_register")
    return _auth_response(user, "Account created")


@router.post("/auth/login", response=AuthResponse)
def login_native(request, data: NativeLoginRequest):
    """Authenticate one Django account using a normalized email identifier."""
    matches = list(
        User.objects.filter(email__iexact=data.email).values_list("username", flat=True)[:2]
    )
    if len(matches) != 1:
        raise HttpError(401, "Invalid authentication credential")

    user = authenticate(request, username=matches[0], password=data.password)
    if user is None or not user.is_active:
        raise HttpError(401, "Invalid authentication credential")

    _open_session(request, user, method="django_password")
    return _auth_response(user, "Authenticated")


@router.get("/auth/me", response=UserResponse)
def current_identity(request):
    return _serialize_user(_require_authenticated(request))


def _logout_principal(request):
    """Resolve the native bearer explicitly: this is a public-auth router.

    Hosted Web Preview forwards Authorization but deliberately strips cookies.
    A 200 logout without a resolved principal would leave its native bearer
    valid until expiry. Never resolve an account from an unverified payload.
    """
    session_user = getattr(request, "user", None)
    if session_user is not None and not session_user.is_authenticated:
        session_user = None

    headers = getattr(request, "headers", None)
    authorization = headers.get("Authorization") if headers is not None else None
    if authorization is None:
        return session_user  # Legacy session-only and idempotent anonymous logout.

    scheme, separator, bearer = authorization.partition(" ")
    if (
        scheme.lower() != "bearer"
        or not separator
        or not bearer
        or bearer != bearer.strip()
    ):
        raise HttpError(401, "Authentication required")
    try:
        bearer_user = verify_native_token(bearer)
    except NativeTokenError as exc:
        raise HttpError(401, "Authentication required") from exc
    if session_user is not None and session_user.pk != bearer_user.pk:
        raise HttpError(401, "Conflicting authentication identities")
    return bearer_user


@router.post("/auth/logout")
def logout_native(request):
    user = _logout_principal(request)
    if user is not None:
        revoke_native_tokens(user)
    logout(request)
    return {"detail": "Signed out"}


@router.post("/auth/password")
@transaction.atomic
def set_native_password(request, data: SetPasswordRequest):
    """Establish or rotate the native credential without weakening ownership."""
    user = _require_authenticated(request)
    if user.has_usable_password():
        if not data.current_password or not user.check_password(data.current_password):
            raise HttpError(401, "Current password is invalid")

    try:
        validate_password(data.new_password, user=user)
    except ValidationError as exc:
        raise HttpError(400, "Password does not meet security requirements") from exc

    user.set_password(data.new_password)
    user.save(update_fields=["password"])
    revoke_native_tokens(user)
    update_session_auth_hash(request, user)
    return {
        "detail": "Django password established",
        "access_token": issue_native_token(user),
        "token_type": "Bearer",
    }


@router.post("/auth/password/reset/request")
def request_password_reset(request, data: PasswordResetRequest):
    """Send a native recovery link without disclosing account existence."""
    users = list(User.objects.filter(email__iexact=data.email, is_active=True)[:2])
    if len(users) == 1 and users[0].has_usable_password():
        user = users[0]
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        base_url = getattr(
            settings,
            "PASSWORD_RESET_FRONTEND_URL",
            "iamina://reset-password",
        )
        separator = "&" if "?" in base_url else "?"
        reset_url = f"{base_url}{separator}uid={uid}&token={token}"
        try:
            sent = send_mail(
                subject="Réinitialisation du mot de passe IAMINA",
                message=(
                    "Utilisez ce lien pour définir un nouveau mot de passe : "
                    f"{reset_url}"
                ),
                from_email=getattr(
                    settings,
                    "DEFAULT_FROM_EMAIL",
                    "noreply@iamina.health",
                ),
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as exc:
            logger.error(
                "Password reset email delivery failed: %s",
                type(exc).__name__,
            )
        else:
            if sent != 1:
                logger.error("Password reset email delivery was not confirmed")
    return {"detail": "If the account exists, the recovery request was accepted"}


@router.post("/auth/password/reset/confirm")
@transaction.atomic
def confirm_password_reset(request, data: PasswordResetConfirmRequest):
    """Consume a one-time Django recovery token and revoke prior IAMINA tokens."""
    try:
        user_id = force_str(urlsafe_base64_decode(data.uid))
        user = User.objects.get(pk=user_id, is_active=True)
    except (ValueError, TypeError, OverflowError, User.DoesNotExist) as exc:
        raise HttpError(400, "Invalid or expired recovery credential") from exc

    if not default_token_generator.check_token(user, data.token):
        raise HttpError(400, "Invalid or expired recovery credential")
    try:
        validate_password(data.new_password, user=user)
    except ValidationError as exc:
        raise HttpError(400, "Password does not meet security requirements") from exc

    user.set_password(data.new_password)
    user.save(update_fields=["password"])
    revoke_native_tokens(user)
    return {"detail": "Password reset completed"}


@router.post("/auth/firebase", response=AuthResponse)
def firebase_auth(request, data: FirebaseAuthRequest):
    """Migrate or resolve one verified Firebase identity, then issue IAMINA auth."""
    try:
        identity = verify_firebase_token(data.id_token)
        user = migrate_new_firebase_identity(identity)
    except FirebaseIdentityConflict as exc:
        raise HttpError(409, "Account linking requires authenticated recovery") from exc
    except FirebaseMigrationError as exc:
        raise HttpError(401, "Invalid authentication credential") from exc

    _open_session(request, user, method="firebase_migration")
    return _auth_response(user, "Authenticated through migration bridge")


@router.post("/auth/firebase/link")
@transaction.atomic
def link_firebase_identity(request, data: FirebaseAuthRequest):
    """Explicitly attach a verified Firebase UID to the current Django account."""
    user = _require_authenticated(request)
    try:
        identity = verify_firebase_token(data.id_token)
    except FirebaseMigrationError as exc:
        raise HttpError(401, "Invalid authentication credential") from exc

    other_link = BasePatientProfile.objects.select_related("patient").filter(
        firebase_uid=identity.uid
    ).first()
    if other_link is not None and other_link.patient_id != user.id:
        raise HttpError(409, "Firebase identity is already linked")

    profile, _ = BasePatientProfile.objects.get_or_create(patient=user)
    if profile.firebase_uid and profile.firebase_uid != identity.uid:
        raise HttpError(409, "A different Firebase identity is already linked")

    normalized_email = user.email.strip().lower() if user.email else ""
    if identity.email:
        if not identity.email_verified:
            raise HttpError(409, "Verified Firebase email required for linking")
        if normalized_email and identity.email != normalized_email:
            raise HttpError(409, "Firebase email does not match the Django account")

    profile.firebase_uid = identity.uid
    profile.save(update_fields=["firebase_uid"])
    return {"detail": "Firebase identity linked"}


@router.delete("/auth/firebase/link")
@transaction.atomic
def unlink_firebase_identity(request):
    """Remove the migration credential only when native recovery is available."""
    user = _require_authenticated(request)
    if not user.has_usable_password():
        raise HttpError(409, "Set a Django password before removing Firebase access")

    try:
        profile = BasePatientProfile.objects.get(patient=user)
    except BasePatientProfile.DoesNotExist:
        return {"detail": "Firebase identity already unlinked"}

    if profile.firebase_uid:
        profile.firebase_uid = None
        profile.save(update_fields=["firebase_uid"])
    return {"detail": "Firebase identity unlinked"}
