"""W01 G5 Preview PostgreSQL identity is read-only and fails closed."""
from unittest.mock import Mock

from amina.preview_db_identity import (
    IDENTITY_SQL,
    PREVIEW_API_PROJECT,
    SYNTHETIC_NEON_BRANCH,
    SYNTHETIC_NEON_PROJECT,
    preview_identity_allowed,
    read_synthetic_identity,
)

HOST = "iamina-certified-example123-achraf-benmoussa-s-projects.vercel.app"
ENV = {
    "VERCEL": "1", "VERCEL_ENV": "preview", "IAMINA_ENV": "development",
    "VERCEL_PROJECT_ID": PREVIEW_API_PROJECT, "VERCEL_URL": HOST,
    "IAMINA_EXPECTED_DB_NAME": "iamina925_empty",
    "IAMINA_EXPECTED_DB_ROLE": "iamina_preview_app",
}
GOOD_ROW = ("iamina925_empty", "iamina_preview_app", SYNTHETIC_NEON_PROJECT, SYNTHETIC_NEON_BRANCH)


def test_exact_preview_only_and_no_sql_eligibility_on_wrong_scope():
    assert preview_identity_allowed(HOST, ENV)
    for k, wrong in (
        ("VERCEL", "0"), ("VERCEL_ENV", "production"),
        ("IAMINA_ENV", "production"), ("VERCEL_PROJECT_ID", "prj_other"),
        ("VERCEL_URL", "iamina-certified-other123-achraf-benmoussa-s-projects.vercel.app")
    ):
        assert not preview_identity_allowed(HOST, {**ENV, k: wrong})
    for host in (
        HOST + ".attacker.test", HOST + ":443", "localhost",
        "iamina-certified.vercel.app",
        "iamina-review-example123-achraf-benmoussa-s-projects.vercel.app", ""
    ):
        assert not preview_identity_allowed(host, ENV)


def test_identity_query_is_read_only():
    cursor = Mock()
    cursor.fetchone.return_value = GOOD_ROW
    assert read_synthetic_identity(cursor, ENV) == {
        "database_name": "iamina925_empty",
        "role_name": "iamina_preview_app",
        "neon_project_id": SYNTHETIC_NEON_PROJECT,
        "neon_branch_id": SYNTHETIC_NEON_BRANCH,
    }
    cursor.execute.assert_called_once_with(IDENTITY_SQL)
    assert IDENTITY_SQL.startswith("SELECT ")
    assert "DATABASE_URL" not in IDENTITY_SQL


def test_wrong_database_role_project_branch_or_no_result_fails_closed():
    for index, value in enumerate(("other_database", "postgres", "other_project", "other_branch")):
        row = list(GOOD_ROW)
        row[index] = value
        cursor = Mock()
        cursor.fetchone.return_value = row
        assert read_synthetic_identity(cursor, ENV) is None
    cursor = Mock()
    cursor.fetchone.return_value = None
    assert read_synthetic_identity(cursor, ENV) is None


def test_missing_expected_config_fails_closed():
    cursor = Mock()
    cursor.fetchone.return_value = GOOD_ROW
    for key in ("IAMINA_EXPECTED_DB_NAME", "IAMINA_EXPECTED_DB_ROLE"):
        assert read_synthetic_identity(cursor, {k: v for k, v in ENV.items() if k != key}) is None
