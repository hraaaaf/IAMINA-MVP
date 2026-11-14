"""D1 native Django identity/fail-closed consent boundary tests.

Actual Django auth user and BasePatientProfile on disposable in-memory SQLite.
NO patient data, no migration grants, no API, no release of a vault lock.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.d1_native_migration_identity_candidate import (
    D1NativeOwnerReview,
    preview_native_legacy_ownership,
)
from core.models import AIConsentReceipt, BasePatientProfile
from core.native_auth import issue_native_token, revoke_native_tokens


class TestD1NativeIdentityBoundary(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="synthetic-d1-owner-a", password="NeverProductionA123!"
        )
        self.bob = User.objects.create_user(
            username="synthetic-d1-owner-b", password="NeverProductionB123!"
        )
        BasePatientProfile.objects.create(patient=self.alice)
        BasePatientProfile.objects.create(patient=self.bob)
        self.alice_token = issue_native_token(self.alice)
        self.alice_db = f"amina_vault_v1_native_{self.alice.pk}"

    def check_denied(self, result: D1NativeOwnerReview):
        self.assertIs(result.authorized_to_migrate, False)
        self.assertIs(result.clinical_go, False)
        self.assertIs(result.migration_consent_verified, False)
        self.assertIs(result.old_vault_possession_verified, False)
        self.assertIs(result.verified_backup_receipt_from_server, False)

    def inspect(self, token=None, source=None, session_user=None):
        return preview_native_legacy_ownership(
            native_token=self.alice_token if token is None else token,
            legacy_store_name=self.alice_db if source is None else source,
            session_user=session_user,
        )

    def test_valid_native_token_proves_scope_but_not_consent(self):
        result = self.inspect()
        self.check_denied(result)
        self.assertIs(result.native_scope_verified, True)
        self.assertEqual(
            result.reason, "D1_MIGRATION_CONSENT_AND_POSSESSION_REGISTRY_NOT_IMPLEMENTED"
        )

    def test_cross_patient_namespace_is_never_assigned(self):
        result = self.inspect(source=f"amina_vault_v1_native_{self.bob.pk}")
        self.check_denied(result)
        self.assertFalse(result.native_scope_verified)
        self.assertEqual(
            result.reason, "D1_SOURCE_NOT_BOUND_TO_VERIFIED_DJANGO_SUBJECT"
        )

    def test_unscoped_amina_database_cannot_be_inferred(self):
        result = self.inspect(source="amina")
        self.check_denied(result)
        self.assertEqual(
            result.reason, "D1_UNSCOPED_LEGACY_STORE_REQUIRES_OWNERSHIP_PROOF"
        )

    def test_firebase_or_cookie_only_is_not_a_native_bearer(self):
        for token in ("", "firebase-unverified", "Bearer iamina.invalid", "eyJxxx.yyy.zzz"):
            result = self.inspect(token=token)
            self.check_denied(result)
            self.assertEqual(result.reason, "D1_NATIVE_BEARER_REQUIRED")

    def test_tampered_native_credential_does_not_resolve(self):
        invalid = self.alice_token + "-tampered"
        result = self.inspect(token=invalid)
        self.check_denied(result)
        self.assertEqual(result.reason, "D1_NATIVE_BEARER_INVALID_OR_REVOKED")

    def test_token_version_revocation_is_enforced_from_real_db(self):
        stale = self.alice_token
        revoke_native_tokens(self.alice)
        result = self.inspect(token=stale)
        self.check_denied(result)
        self.assertEqual(result.reason, "D1_NATIVE_BEARER_INVALID_OR_REVOKED")
        fresh = issue_native_token(self.alice)
        new_result = self.inspect(token=fresh)
        self.check_denied(new_result)
        self.assertTrue(new_result.native_scope_verified)

    def test_deactivated_native_django_user_cannot_verify_bearer(self):
        self.alice.is_active = False
        self.alice.save(update_fields=["is_active"])
        result = self.inspect()
        self.check_denied(result)
        self.assertEqual(result.reason, "D1_NATIVE_BEARER_INVALID_OR_REVOKED")

    def test_conflicting_cookie_principal_fails_before_consent(self):
        result = self.inspect(session_user=self.bob)
        self.check_denied(result)
        self.assertEqual(result.reason, "D1_COOKIE_NATIVE_IDENTITY_CONFLICT")
        own_cookie = self.inspect(session_user=self.alice)
        self.check_denied(own_cookie)
        self.assertTrue(own_cookie.native_scope_verified)

    def test_device_owner_needs_separate_possession_flow(self):
        result = self.inspect(
            source="amina_vault_v1_device_1234567841234abc8abcdef012345678"
        )
        self.check_denied(result)
        self.assertEqual(
            result.reason, "D1_SOURCE_NOT_BOUND_TO_VERIFIED_DJANGO_SUBJECT"
        )

    def test_even_existing_ai_consent_cannot_approve_vault_migration(self):
        profile = self.alice.base_profile
        profile.ai_consent_given_at = timezone.now()
        profile.ai_consent_notice_version = "2026-09-12.1"
        profile.ai_consent_notice_hash = "a" * 64
        profile.ai_consent_notice_locale = "fr"
        profile.save()
        AIConsentReceipt.objects.create(
            patient=self.alice,
            notice_version="2026-09-12.1",
            notice_hash="a" * 64,
            notice_locale="fr",
            granted_at=timezone.now(),
        )
        self.assertTrue(AIConsentReceipt.objects.filter(patient=self.alice).exists())
        result = self.inspect()
        self.check_denied(result)
        self.assertTrue(result.native_scope_verified)
        self.assertEqual(
            result.reason, "D1_MIGRATION_CONSENT_AND_POSSESSION_REGISTRY_NOT_IMPLEMENTED"
        )

    def test_readonly_preview_never_creates_accounts_or_profiles(self):
        before_users = User.objects.count()
        before_profiles = BasePatientProfile.objects.count()
        for store in (
            self.alice_db,
            f"amina_vault_v1_native_{self.bob.pk}",
            "amina",
            "amina_vault_v1_device_1234567841234abc8abcdef012345678",
        ):
            self.check_denied(self.inspect(source=store))
        self.assertEqual(User.objects.count(), before_users)
        self.assertEqual(BasePatientProfile.objects.count(), before_profiles)

    def test_missing_profile_rejects_authenticated_claim_without_creating(self):
        profile = BasePatientProfile.objects.get(patient=self.alice)
        profile.delete()
        before = BasePatientProfile.objects.count()
        result = self.inspect()
        self.check_denied(result)
        self.assertEqual(result.reason, "D1_NATIVE_BEARER_INVALID_OR_REVOKED")
        self.assertEqual(BasePatientProfile.objects.count(), before)
