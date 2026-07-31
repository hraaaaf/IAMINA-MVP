"""Authentication migration endpoints.

POST /api/v1/auth/firebase verifies one Firebase credential and migrates a
previously unseen identity through the controlled bridge. Firebase remains a
temporary migration credential; Django ``User`` is authoritative.
"""

from django.contrib.auth import login
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, ConfigDict

from core.auth_migration import (
    FirebaseIdentityConflict,
    FirebaseMigrationError,
    migrate_new_firebase_identity,
    verify_firebase_token,
)
from core.observability import EVT_SESSION_START, track

router = Router(tags=["auth"])


class FirebaseAuthRequest(BaseModel):
    id_token: str


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
    """Migrate or resolve one verified Firebase identity, then open a session."""
    try:
        identity = verify_firebase_token(data.id_token)
        user = migrate_new_firebase_identity(identity)
    except FirebaseIdentityConflict as exc:
        raise HttpError(409, "Account linking requires authenticated recovery") from exc
    except FirebaseMigrationError as exc:
        raise HttpError(401, "Invalid authentication credential") from exc

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    track(EVT_SESSION_START, patient_id=user.id, props={"method": "firebase_migration"})

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "created_at": user.date_joined.isoformat(),
        },
        "message": "Authenticated through migration bridge",
    }
