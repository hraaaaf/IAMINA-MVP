"""W01 G5: non-secret, fail-closed Preview-only DB identity proof."""
from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any

PREVIEW_API_PROJECT = "prj_Pn9FnyconF3h2w9gOU74iV98kJoU"
SYNTHETIC_NEON_PROJECT = "noisy-truth-00115950"
SYNTHETIC_NEON_BRANCH = "br-sweet-frog-b9ok6ptp"
_PREVIEW_HOST = re.compile(
    r"iamina-certified-[a-z0-9]+-achraf-benmoussa-s-projects\.vercel\.app\Z"
)
IDENTITY_SQL = (
    "SELECT current_database(), current_user, "
    "current_setting('neon.project_id', true), "
    "current_setting('neon.branch_id', true)"
)

def preview_identity_allowed(host: str, env: Mapping[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return bool(
        values.get("VERCEL") == "1"
        and values.get("VERCEL_ENV") == "preview"
        and values.get("IAMINA_ENV") == "development"
        and values.get("VERCEL_PROJECT_ID") == PREVIEW_API_PROJECT
        and isinstance(host, str)
        and _PREVIEW_HOST.fullmatch(host)
        and host == values.get("VERCEL_URL")
    )

def read_synthetic_identity(cursor: Any, env: Mapping[str, str] | None = None) -> dict[str, str] | None:
    """Read actual SQL session; refuse any mismatch without leaking it."""
    values = os.environ if env is None else env
    cursor.execute(IDENTITY_SQL)
    row = cursor.fetchone()
    if row is None or len(row) != 4:
        return None
    database, role, neon_project, neon_branch = row
    if (
        not isinstance(database, str)
        or not isinstance(role, str)
        or not isinstance(neon_project, str)
        or not isinstance(neon_branch, str)
        or not database
        or not role
        or database != values.get("IAMINA_EXPECTED_DB_NAME")
        or role != values.get("IAMINA_EXPECTED_DB_ROLE")
        or neon_project != SYNTHETIC_NEON_PROJECT
        or neon_branch != SYNTHETIC_NEON_BRANCH
    ):
        return None
    return {
        "database_name": database,
        "role_name": role,
        "neon_project_id": neon_project,
        "neon_branch_id": neon_branch,
    }
