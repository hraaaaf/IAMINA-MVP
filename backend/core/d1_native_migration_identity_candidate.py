"""D1/J2 no-route native identity evidence preview. NEVER authorizes migration.

Uses existing Django sovereign/native token verification, which resolves a
single linked, active Django User and checks profile auth_token_version.
This is not an API and accepts no Firebase or cookie-only substitute.

There is no audited, dedicated consent-for-legacy-vault-migration record or
old-vault-possession verifier wired to Django at this time. AI consent is a
different purpose and MUST NEVER be substituted. Therefore this module is
intentionally incapable of issuing a receipt or authorizing a patient migration.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.native_auth import NativeTokenError, verify_native_token


@dataclass(frozen=True, slots=True)
class D1NativeOwnerReview:
    reason: str
    native_scope_verified: bool = False
    migration_consent_verified: bool = False
    old_vault_possession_verified: bool = False
    verified_backup_receipt_from_server: bool = False
    authorized_to_migrate: bool = False
    clinical_go: bool = False


def _deny(reason: str, *, native_scope_verified: bool = False) -> D1NativeOwnerReview:
    return D1NativeOwnerReview(
        reason=reason, native_scope_verified=native_scope_verified,
    )


def preview_native_legacy_ownership(
    *, native_token: str, legacy_store_name: str, session_user=None,
) -> D1NativeOwnerReview:
    """Read-only identity boundary. No DB writes, no grants, no inferred owner.

    session_user must be the actual Django cookie principal supplied by a
    trusted framework caller, not a client-provided user ID. It is optional
    because verified native Bearer auth does not require cookies.
    """
    if not isinstance(native_token, str) or not native_token.startswith("iamina."):
        return _deny("D1_NATIVE_BEARER_REQUIRED")
    try:
        subject = verify_native_token(native_token)
    except NativeTokenError:
        return _deny("D1_NATIVE_BEARER_INVALID_OR_REVOKED")
    # No bearer/cookie ambiguity; never silently select one account.
    if session_user is not None and getattr(session_user, "is_authenticated", False):
        if getattr(session_user, "pk", None) != getattr(subject, "pk", None):
            return _deny("D1_COOKIE_NATIVE_IDENTITY_CONFLICT")
    # The unscoped old database has NO verified owner. Device-only installs
    # need separate device-possession enrollment, not a guessed Django userId.
    if legacy_store_name == "amina":
        return _deny("D1_UNSCOPED_LEGACY_STORE_REQUIRES_OWNERSHIP_PROOF")
    if isinstance(getattr(subject, "pk", None), bool) or not isinstance(subject.pk, int):
        return _deny("D1_DJANGO_SUBJECT_INVALID")
    if getattr(subject, "is_active", False) is not True:
        return _deny("D1_DJANGO_SUBJECT_INACTIVE")
    exact_owner = f"amina_vault_v1_native_{subject.pk}"
    if legacy_store_name != exact_owner:
        return _deny("D1_SOURCE_NOT_BOUND_TO_VERIFIED_DJANGO_SUBJECT")
    # The native identity is verified at this point. A legacy patient data
    # migration requires additional purpose-specific evidence. AI Consent
    # Receipt fields (ai_consent_*) or cookies are NEVER sufficient.
    return _deny(
        "D1_MIGRATION_CONSENT_AND_POSSESSION_REGISTRY_NOT_IMPLEMENTED",
        native_scope_verified=True,
    )
