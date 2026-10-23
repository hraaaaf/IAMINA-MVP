"""Narrow exemption for intentionally Redis-less W01 synthetic Preview erasure.

No patient/production erasure may use this path. The synthetic Preview has no
REDIS_URL configured: document-ingest cannot persist pending extraction batches
and returns 503. Only W01 G5 generated identities are eligible. This does NOT
change behavior for configured but unavailable Redis installations.
"""
from __future__ import annotations

import os
import re
from collections.abc import Mapping

from django.contrib.auth.models import User

EXPECTED_API_PROJECT = "prj_Pn9FnyconF3h2w9gOU74iV98kJoU"
EXPECTED_DB_HOST = "ep-old-art-b9sy0oo4.c-7.eu-central-1.aws.neon.tech"
EXPECTED_DB_NAME = "iamina925_empty"
EXPECTED_DB_ROLE = "iamina_preview_app"
_SYNTHETIC_EMAIL = re.compile(r"w01g5-bff-[0-9a-f]{20}@example\.invalid\Z")


def synthetic_preview_without_redis(env: Mapping[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return (
        values.get("VERCEL") == "1"
        and values.get("VERCEL_ENV") == "preview"
        and values.get("IAMINA_ENV") == "development"
        and values.get("VERCEL_PROJECT_ID") == EXPECTED_API_PROJECT
        and values.get("IAMINA_EXPECTED_DB_HOST") == EXPECTED_DB_HOST
        and values.get("IAMINA_EXPECTED_DB_NAME") == EXPECTED_DB_NAME
        and values.get("IAMINA_EXPECTED_DB_ROLE") == EXPECTED_DB_ROLE
        and "REDIS_URL" not in values
    )


def can_erase_synthetic_without_cache(
    patient_id: int, firebase_uid: str, env: Mapping[str, str] | None = None
) -> bool:
    """May fail open for one impossible-to-cache W01 synthetic identity only.

    The normal fail-closed cleanup executes first; this is a narrowly audited
    fallback when the unconfigured localhost-only Redis backend is unreachable.
    """
    if not synthetic_preview_without_redis(env) or firebase_uid:
        return False
    if type(patient_id) is not int or patient_id <= 0:
        return False

    user = User.objects.filter(pk=patient_id).only(
        "id", "username", "email", "first_name", "last_name"
    ).first()
    if user is None or not _SYNTHETIC_EMAIL.fullmatch(user.email):
        return False
    if (
        user.username != user.email
        or user.first_name != "Synthetic"
        or user.last_name not in {"W01-A", "W01-B"}
    ):
        return False

    from core.models import BasePatientProfile
    from diabetes.models import LabReport, LogEntry

    profile = BasePatientProfile.objects.filter(patient_id=patient_id).first()
    if profile is None or profile.firebase_uid:
        return False
    if LabReport.objects.filter(patient_id=patient_id).exists():
        return False
    if LogEntry.objects.filter(patient_id=patient_id).exists():
        return False
    return True
