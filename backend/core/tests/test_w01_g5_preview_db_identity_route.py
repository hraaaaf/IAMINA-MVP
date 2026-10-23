"""Route contract: no SQL for non-Preview; no metadata leakage on mismatch."""
import json
from unittest.mock import Mock, patch
from django.test import RequestFactory
from amina.preview_db_identity import PREVIEW_API_PROJECT, SYNTHETIC_NEON_BRANCH, SYNTHETIC_NEON_PROJECT
from core.api.v1.health import preview_db_identity

HOST = "iamina-certified-exact123-achraf-benmoussa-s-projects.vercel.app"
ENV = {
    "VERCEL": "1", "VERCEL_ENV": "preview", "IAMINA_ENV": "development",
    "VERCEL_PROJECT_ID": PREVIEW_API_PROJECT, "VERCEL_URL": HOST,
    "IAMINA_EXPECTED_DB_NAME": "iamina925_empty",
    "IAMINA_EXPECTED_DB_ROLE": "iamina_preview_app",
}


def _fake_cursor(row):
    cursor = Mock()
    cursor.fetchone.return_value = row
    ctx = Mock()
    ctx.__enter__ = Mock(return_value=cursor)
    ctx.__exit__ = Mock(return_value=False)
    return ctx


def test_production_returns_404_before_any_sql():
    req = RequestFactory().get("/api/v1/ops/preview-db-identity", HTTP_HOST=HOST)
    with patch.dict("os.environ", {**ENV, "VERCEL_ENV": "production"}), patch("core.api.v1.health.connection.cursor") as cursor:
        response = preview_db_identity(req)
    assert response.status_code == 404
    assert json.loads(response.content) == {"detail": "Not Found"}
    cursor.assert_not_called()
    assert response["Cache-Control"] == "private, no-store"


def test_preview_reads_sql_session_identity():
    req = RequestFactory().get("/api/v1/ops/preview-db-identity", HTTP_HOST=HOST)
    row = ("iamina925_empty", "iamina_preview_app", SYNTHETIC_NEON_PROJECT, SYNTHETIC_NEON_BRANCH)
    with patch.dict("os.environ", ENV), patch("core.api.v1.health.connection.cursor", return_value=_fake_cursor(row)):
        response = preview_db_identity(req)
    assert response.status_code == 200
    assert json.loads(response.content)["neon_branch_id"] == SYNTHETIC_NEON_BRANCH
    assert response["Cache-Control"] == "private, no-store"


def test_mismatched_sql_session_returns_503_without_details():
    req = RequestFactory().get("/api/v1/ops/preview-db-identity", HTTP_HOST=HOST)
    row = ("wrong_database", "iamina_preview_app", SYNTHETIC_NEON_PROJECT, SYNTHETIC_NEON_BRANCH)
    with patch.dict("os.environ", ENV), patch("core.api.v1.health.connection.cursor", return_value=_fake_cursor(row)):
        response = preview_db_identity(req)
    assert response.status_code == 503
    assert json.loads(response.content) == {"detail": "Unavailable"}
    assert "wrong_database" not in response.content.decode()
