"""D1 Safari HTTPS Preview contract, synthetic-only. No device claims."""
import json

import pytest
from django.test import Client, override_settings

from core.models import BasePatientProfile


@pytest.mark.django_db
def test_safari_preview_bootstrap_and_route_isolation():
    with override_settings(
        ROOT_URLCONF="d1_safari_preview.urls",
        D1_PASSKEY_RESEARCH_ENABLED=True,
    ):
        client = Client(enforce_csrf_checks=True)
        assert client.get("/admin/").status_code == 404
        assert client.get("/api/v1/patients").status_code in {404, 405}
        page = client.get("/d1-research/safari/")
        assert page.status_code == 200
        assert b"PATIENT NO-GO" in page.content
        assert b"labStart" in page.content
        assert "default-src 'none'" in page["Content-Security-Policy"]
        for asset in ("client.js", "bridge.js", "lab.css"):
            result = client.get("/d1-research/safari/" + asset)
            assert result.status_code == 200
            assert result["Cache-Control"] == "no-store"
            assert result["X-Content-Type-Options"] == "nosniff"
        assert client.get("/d1-research/safari/notfound").status_code == 404

        no_csrf = client.post(
            "/d1-research/lab/start",data="{}",content_type="application/json",
        )
        assert no_csrf.status_code == 403
        csrf = client.get("/csrf/").json()["csrf_token"]
        boot = client.post(
            "/d1-research/lab/start",data="{}",content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert boot.status_code == 200
        data = boot.json()
        assert data["status"] == "SYNTHETIC_LAB_CREATED"
        assert data["patient_ready"] is False
        assert len(data["enrollment_password"]) >= 24
        assert BasePatientProfile.objects.filter(
            patient__username__startswith="d1lab_",
        ).count() == 1
        assert boot["Cache-Control"] == "no-store"
        assert client.session["d1lab_synthetic_user"] > 0

        csrf = client.get("/csrf/").json()["csrf_token"]
        again = client.post(
            "/d1-research/lab/start",data="{}",content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert again.status_code == 200
        assert again.json() == {"status": "ALREADY_STARTED", "patient_ready": False}
        assert "enrollment_password" not in again.json()
        assert client.get("/api/v1/patients").status_code in {404, 405}


@pytest.mark.django_db
def test_safari_preview_research_route_denies_other_accounts():
    with override_settings(
        ROOT_URLCONF="d1_safari_preview.urls",
        D1_PASSKEY_RESEARCH_ENABLED=True,
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "d1_safari_preview.views.SyntheticAccountOnlyMiddleware",
        ],
    ):
        client = Client(enforce_csrf_checks=True)
        csrf = client.get("/csrf/").json()["csrf_token"]
        denied = client.post(
            "/api/v1/d1-research/passkey/session-context",
            data=json.dumps({"credential_id": "dGVzdA"}),
            content_type="application/json",HTTP_X_CSRFTOKEN=csrf,
        )
        assert denied.status_code in (401, 403)
        assert "patient" not in denied.content.decode().lower()


def test_safari_preview_fails_closed_if_feature_off():
    with override_settings(
        ROOT_URLCONF="d1_safari_preview.urls",D1_PASSKEY_RESEARCH_ENABLED=False,
    ):
        assert Client().get("/d1-research/safari/").status_code == 404
        assert Client().post("/d1-research/lab/start").status_code == 404


def test_production_urlconf_does_not_expose_safari_preview():
    with override_settings(ROOT_URLCONF="amina.urls",D1_PASSKEY_RESEARCH_ENABLED=False):
        assert Client().get("/d1-research/safari/").status_code == 404
