"""Temporary Firebase bearer authentication during Django auth migration.

This authenticator may resolve only an already-linked Firebase UID. It must not
create, merge or repair Django identities. All migration writes belong to the
controlled bridge in ``core.auth_migration``.
"""

import logging
import os

import firebase_admin
from firebase_admin import credentials
from ninja.security import HttpBearer

from core.auth_migration import (
    FirebaseIdentityNotLinked,
    FirebaseMigrationError,
    resolve_linked_firebase_user,
    verify_firebase_token,
)

logger = logging.getLogger(__name__)

if not firebase_admin._apps:
    credential_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    if credential_path and os.path.exists(credential_path):
        credential = credentials.Certificate(credential_path)
    else:
        credential = credentials.ApplicationDefault()
    firebase_admin.initialize_app(credential)


class FirebaseAuth(HttpBearer):
    """Resolve one existing Firebase-to-Django link without side effects."""

    def authenticate(self, request, token: str):
        try:
            identity = verify_firebase_token(token)
            user = resolve_linked_firebase_user(identity)
        except FirebaseIdentityNotLinked:
            logger.warning("Firebase bearer rejected: identity is not linked")
            return None
        except FirebaseMigrationError:
            logger.warning("Firebase bearer rejected: invalid credential")
            return None

        request.user = user
        return user


firebase_auth_backend = FirebaseAuth()
