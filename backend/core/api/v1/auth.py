"""
Authentication endpoints — Firebase JWT verification & user linking.
POST /api/v1/auth/firebase — Bridge Firebase JWT to Django User

Security contract:
  - id_token is ALWAYS verified via Firebase Admin SDK (verify_id_token).
  - User lookup is keyed on firebase_uid (stable), NOT email (mutable).
  - Email is synced on each login in case the user changed it in Firebase.
  - 401 is returned on any token verification failure (expired, revoked, malformed).
"""

from datetime import date
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
         Fall back to email lookup for existing accounts not yet migrated.
      4. Create user + profile if brand new.
      5. Sync firebase_uid + email on every login (they can change in Firebase).
      6. Establish Django session for web/PWA clients.
    """
    # ── Step 1: Verify token ──────────────────────────────────────────────────
    try:
        from firebase_admin import auth as fb_auth
        decoded = fb_auth.verify_id_token(data.id_token)
    except Exception as exc:
        raise HttpError(401, f"Invalid Firebase token: {exc}") from exc

    uid   = decoded["uid"]
    email = decoded.get("email") or ""

    # ── Step 2: Resolve Django User ───────────────────────────────────────────
    user = _resolve_user(uid, email)

    # ── Step 3: Sync session ──────────────────────────────────────────────────
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    track(EVT_SESSION_START, patient_id=user.id, props={"method": "firebase"})

    return {
        "user": {
            "id":         user.id,
            "email":      user.email,
            "first_name": user.first_name,
            "last_name":  user.last_name,
            "created_at": user.date_joined.isoformat(),
        },
        "message": "Authenticated via Firebase",
    }


# ── helpers ───────────────────────────────────────────────────────────────────

def _resolve_user(uid: str, email: str) -> User:
    """
    Find or create a Django User for the given Firebase uid.

    Lookup order:
      1. BasePatientProfile.firebase_uid == uid  (fast, index-backed, stable)
      2. User.username == uid                    (migration: user created by security.py)
      3. User.email == email                     (migration: user created before UID tracking)
      4. Create new user

    Always ensures firebase_uid is recorded on BasePatientProfile after resolution.
    """
    # 1. Primary key: firebase_uid on BasePatientProfile
    try:
        base = BasePatientProfile.objects.select_related("patient").get(firebase_uid=uid)
        user = base.patient
        _sync_email(user, email)
        return user
    except BasePatientProfile.DoesNotExist:
        pass

    # 2. Username == uid (created by FirebaseAuth bearer in security.py)
    try:
        user = User.objects.get(username=uid)
        _sync_email(user, email)
        _ensure_profile(user, uid)
        return user
    except User.DoesNotExist:
        pass

    # 3. Email migration (legacy accounts created before UID tracking)
    if email:
        try:
            user = User.objects.get(email=email)
            _sync_email(user, email)
            _ensure_profile(user, uid)
            return user
        except User.DoesNotExist:
            pass

    # 4. New user — two-step creation: BasePatientProfile first, then DiabetesProfile
    base_username = (email.split("@")[0] if email else uid[:16])
    username = _unique_username(base_username)
    user = User.objects.create_user(username=username, email=email)
    base = BasePatientProfile.objects.create(
        patient=user,
        firebase_uid=uid,
        date_of_birth=date(1980, 1, 1),
    )
    DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type="type2",
        treatment_type="oral_meds",
    )
    return user


def _sync_email(user: User, email: str) -> None:
    """Keep Django email in sync with Firebase (user may update it there)."""
    if email and user.email != email:
        user.email = email
        user.save(update_fields=["email"])


def _ensure_profile(user: User, uid: str) -> None:
    """Create BasePatientProfile + DiabetesProfile if missing; always set firebase_uid."""
    base, created = BasePatientProfile.objects.get_or_create(
        patient=user,
        defaults={
            "firebase_uid": uid,
            "date_of_birth": date(1980, 1, 1),
        },
    )
    if not base.firebase_uid:
        base.firebase_uid = uid
        base.save(update_fields=["firebase_uid"])
    # Ensure DiabetesProfile exists
    DiabetesProfile.objects.get_or_create(
        base_profile=base,
        defaults={
            "diabetes_type": "type2",
            "treatment_type": "oral_meds",
        },
    )


def _unique_username(base: str) -> str:
    """Append a counter suffix until the username is free."""
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}_{counter}"
        counter += 1
    return username
