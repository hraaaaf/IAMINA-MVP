import logging
import os

import firebase_admin
from django.contrib.auth import get_user_model
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from ninja.security import HttpBearer

logger = logging.getLogger(__name__)

# Initialiser Firebase Admin une seule fois
if not firebase_admin._apps:
    cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
    else:
        # Fallback to default or warning
        cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

User = get_user_model()

class FirebaseAuth(HttpBearer):
    """
    Real Firebase JWT Authenticator using Firebase Admin SDK.
    """
    def authenticate(self, request, token: str):
        try:
            decoded = firebase_auth.verify_id_token(token)
            uid   = decoded['uid']
            email = decoded.get('email', '')

            # Link to Django User
            user, _ = User.objects.get_or_create(
                username=uid,
                defaults={'email': email}
            )
            request.user = user
            return user
        except Exception as e:
            logger.error(f"FirebaseAuth: Token verification failed: {e}")
            return None

firebase_auth_backend = FirebaseAuth()
