"""
Authentication endpoints — Firebase JWT verification & user linking.
POST /api/v1/auth/firebase — Bridge Firebase JWT to Django User

Security / integrity contract:
  - id_token is ALWAYS verified via Firebase Admin SDK (verify_id_token).
  - User lookup is keyed on firebase_uid (stable), NOT email (mutable).
  - Email is synced on each login in case the user changed it in Firebase.
  - 401 is returned on any token verification failure (expired, revoked, malformed).
  - Authentication creates identity/profile shells only. It MUST NOT invent DOB,
    gender, diabetes type, treatment, diagnosis, or any other patient fact.
"""
from typing import Optional

from django.contrib.auth import login
from django.contrib.auth.models import User
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, ConfigDict

from core.models import BasePatientProfile
from core.observability import EVT_SESSION_START, track
from diabetes.models import DiabetesProfile

router = Router(tags=["auth"])


class FirebaseAuthRequest(BaseModel):
    id_token: str
    email: Optional[str] = None   # kept for schema compat; ignored — email comes from JWT


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


@router.post("/auth/firebase", response=AuthResponse)
def firebase_auth(request, data: FirebaseAuthRequest):
    """
    Verify Firebase JWT and link/create Django User.

    Flow:
      1. Verify id_token with Firebase Admin SDK → raises 401 on failure.
      2. Extract uid (stable) + email from decoded payload.
      3. Look up Django User by firebase_uid on BasePatientProfile (stable key).
         Fall back to username/email for legacy identities.
      4. Create identity + empty profile shells if brand new.
      5. Sync firebase_uid + email on every login.
      6. Establish Django session for web/PWA clients.

    Clinical/demographic fields remain NULL until explicitly declared.
    """
    try:
        from firebase_admin import auth as fb_auth
        decoded = fb_auth.verify_id_token(data.id_token)
    except Exception as exc:
        raise HttpError(401, f"Invalid Firebase token: {exc}") from exc

    uid = decoded["uid"]
    email = decoded.get("email") or ""

    user = _resolve_user(uid, email)

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    track(EVT_SESSION_START, patient_id=user.id, props={"method": "firebase"})

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "created_at": user.date_joined.isoformat(),
        },
        "message": "Authenticated via Firebase",
    }


def _resolve_user(uid: str, email: str) -> User:
    """Find or create a Django identity without fabricating patient facts."""
    try:
        base = BasePatientProfile.objects.select_related("patient").get(firebase_uid=uid)
        user = base.patient
        _sync_email(user, email)
        _ensure_profile(user, uid)
        return user
    except BasePatientProfile.DoesNotExist:
        pass

    # Legacy bearer bridge historically created username == Firebase UID.
    try:
        user = User.objects.get(username=uid)
        _sync_email(user, email)
        _ensure_profile(user, uid)
        return user
    except User.DoesNotExist:
        pass

    # Legacy email fallback is migration-only. Firebase UID becomes authoritative
    # immediately after resolution.
    if email:
        try:
            user = User.objects.get(email=email)
            _sync_email(user, email)
            _ensure_profile(user, uid)
            return user
        except User.DoesNotExist:
            pass

    base_username = email.split("@")[0] if email else uid[:16]
    username = _unique_username(base_username)
    user = User.objects.create_user(username=username, email=email)
    base = BasePatientProfile.objects.create(patient=user, firebase_uid=uid)
    DiabetesProfile.objects.create(base_profile=base)
    return user


def _sync_email(user: User, email: str) -> None:
    """Keep Django email in sync with Firebase (user may update it there)."""
    if email and user.email != email:
        user.email = email
        user.save(update_fields=["email"])


def _ensure_profile(user: User, uid: str) -> None:
    """Ensure empty identity/module shells exist; never synthesize patient facts."""
    base, _ = BasePatientProfile.objects.get_or_create(
        patient=user,
        defaults={"firebase_uid": uid},
    )
    if not base.firebase_uid:
        base.firebase_uid = uid
        base.save(update_fields=["firebase_uid"])

    DiabetesProfile.objects.get_or_create(base_profile=base)


def _unique_username(base: str) -> str:
    """Append a counter suffix until the username is free."""
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}_{counter}"
        counter += 1
    return username
