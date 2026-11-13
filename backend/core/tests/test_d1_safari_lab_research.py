"""Access and fail-closed contract for D1 Safari test-only pages.

No browser or PRF physical verification is claimed here.
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings

from core.models import BasePatientProfile


@pytest.mark.django_db
def test_safari_lab_requires_authenticated_synthetic_django_session():
    with override_settings(
        ROOT_URLCONF="core.tests.d1_passkey_test_urls",
        D1_PASSKEY_RESEARCH_ENABLED=True,
    ):
        client = Client()
        for path in (
            "/d1-research/safari/",
            "/d1-research/safari/client.js",
            "/d1-research/safari/bridge.js",
            "/d1-research/safari/lab.css",
        ):
            assert client.get(path).status_code == 404
        user = User.objects.create_user(
            username="d1_safari_ui_synthetic",
            password="synthetic-only-no-patient",
        )
        BasePatientProfile.objects.create(patient=user)
        client.force_login(user)
        page = client.get("/d1-research/safari/")
        assert page.status_code == 200
        assert b"Safari + Django + PRF" in page.content
        assert b"PATIENT NO-GO" in page.content
        for path in (
            "/d1-research/safari/client.js",
            "/d1-research/safari/bridge.js",
            "/d1-research/safari/lab.css",
        ):
            response = client.get(path)
            assert response.status_code == 200, path
            assert response["Cache-Control"] == "no-store"
            assert response["Referrer-Policy"] == "no-referrer"
            assert response["X-Content-Type-Options"] == "nosniff"
            assert "script-src 'self'" in response["Content-Security-Policy"]
            assert "connect-src 'self'" in response["Content-Security-Policy"]
        assert client.get("/d1-research/safari/../../api").status_code == 404
        assert client.get("/d1-research/safari/unknown").status_code == 404


@pytest.mark.django_db
def test_safari_lab_is_off_when_feature_flag_is_disabled():
    with override_settings(
        ROOT_URLCONF="core.tests.d1_passkey_test_urls",
        D1_PASSKEY_RESEARCH_ENABLED=False,
    ):
        user = User.objects.create_user(
            username="d1_safari_disabled",
            password="synthetic-only",
        )
        client = Client()
        client.force_login(user)
        assert client.get("/d1-research/safari/").status_code == 404
        assert client.get("/d1-research/safari/client.js").status_code == 404


def test_safari_lab_not_mounted_on_production_urlconf():
    with override_settings(
        ROOT_URLCONF="amina.urls",
        D1_PASSKEY_RESEARCH_ENABLED=False,
    ):
        client = Client()
        assert client.get("/d1-research/safari/").status_code == 404
