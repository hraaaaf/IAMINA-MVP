"""Hybrid bearer authentication during sovereign-auth migration.

IAMINA native tokens are resolved first. Firebase remains a temporary fallback
and may resolve only an already-linked UID. Neither path may create, merge or
repair Django identities.
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
from core.native_auth import NativeTokenError, verify_native_token

logger = logging.getLogger(__name__)

if not firebase_admin._apps:
    credential_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    if credential_path and os.path.exists(credential_path):
        credential = credentials.Certificate(credential_path)
    else:
        credential = credentials.ApplicationDefault()
    firebase_admin.initialize_app(credential)


class HybridBearerAuth(HttpBearer):
    """Resolve sovereign IAMINA tokens, then temporary linked Firebase tokens."""

    def authenticate(self, request, token: str):
        if token.startswith("iamina."):
            try:
                user = verify_native_token(token)
            except NativeTokenError:
                logger.warning("IAMINA bearer rejected: invalid or revoked credential")
                return None
            request.user = user
            return user

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


# Compatibility alias while imports migrate; implementation is hybrid and native-first.
FirebaseAuth = HybridBearerAuth
firebase_auth_backend = HybridBearerAuth()
