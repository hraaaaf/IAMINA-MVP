"""Mobile Safari's Origin:null path remains CSRF protected, Preview-only."""
import pytest
from django.test import Client, override_settings


_PREVIEW_MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "d1_safari_preview.csrf_compat.SafariNullOriginCsrfGuard",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "d1_safari_preview.views.SyntheticAccountOnlyMiddleware",
]
_SCOPED_SETTINGS = {
    "ROOT_URLCONF": "d1_safari_preview.urls",
    "D1_PASSKEY_RESEARCH_ENABLED": True,
    "D1_PASSKEY_RESEARCH_RP_ID": "testserver",
    "D1_PASSKEY_RESEARCH_ORIGIN": "https://testserver",
    "ALLOWED_HOSTS": ["testserver"],
    "CSRF_TRUSTED_ORIGINS": ["https://testserver"],
    "MIDDLEWARE": _PREVIEW_MIDDLEWARE,
}


def _bootstrap(client, csrf, **headers):
    return client.post(
        "/d1-research/lab/start",
        data="{}",
        content_type="application/json",
        secure=True,
        HTTP_X_CSRFTOKEN=csrf,
        HTTP_ORIGIN="null",
        **headers,
    )


@pytest.mark.django_db
def test_safari_null_origin_with_same_origin_fetch_metadata_is_accepted():
    with override_settings(**_SCOPED_SETTINGS):
        client = Client(enforce_csrf_checks=True)
        csrf_resp = client.get("/csrf/", secure=True)
        csrf = csrf_resp.json()["csrf_token"]
        success = _bootstrap(
            client, csrf,
            HTTP_SEC_FETCH_SITE="same-origin",
            HTTP_SEC_FETCH_MODE="cors",
        )
        assert success.status_code == 200, success.content[:200]
        assert success.json()["status"] == "SYNTHETIC_LAB_CREATED"
        assert success.json()["patient_ready"] is False


@pytest.mark.django_db
def test_null_origin_missing_or_bad_csrf_is_rejected_even_same_origin_fetch():
    with override_settings(**_SCOPED_SETTINGS):
        client = Client(enforce_csrf_checks=True)
        client.get("/csrf/", secure=True)
        response = _bootstrap(
            client, "wrong",
            HTTP_SEC_FETCH_SITE="same-origin",
            HTTP_SEC_FETCH_MODE="cors",
        )
        assert response.status_code == 403
        assert client.session.get("d1lab_synthetic_user") is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "metadata",
    [
        {"HTTP_SEC_FETCH_SITE": "cross-site", "HTTP_SEC_FETCH_MODE": "cors"},
        {"HTTP_SEC_FETCH_SITE": "same-site", "HTTP_SEC_FETCH_MODE": "cors"},
        {"HTTP_SEC_FETCH_SITE": "none", "HTTP_SEC_FETCH_MODE": "cors"},
        {"HTTP_SEC_FETCH_SITE": "same-origin", "HTTP_SEC_FETCH_MODE": "navigate"},
        {
            "HTTP_SEC_FETCH_SITE": "same-origin",
            "HTTP_SEC_FETCH_MODE": "cors",
            "HTTP_REFERER": "https://evil.example/d1-research/safari/",
        },
    ],
)
def test_safari_null_origin_unsafe_fetch_evidence_is_denied(metadata):
    with override_settings(**_SCOPED_SETTINGS):
        client = Client(enforce_csrf_checks=True)
        csrf = client.get("/csrf/", secure=True).json()["csrf_token"]
        response = _bootstrap(client, csrf, **metadata)
        assert response.status_code == 403


@pytest.mark.django_db
def test_safari_null_origin_without_fetch_metadata_requires_exact_lab_referer():
    with override_settings(**_SCOPED_SETTINGS):
        client = Client(enforce_csrf_checks=True)
        csrf = client.get("/csrf/", secure=True).json()["csrf_token"]
        assert _bootstrap(client, csrf).status_code == 403
        good = _bootstrap(
            client, csrf,
            HTTP_REFERER="https://testserver/d1-research/safari/",
        )
        assert good.status_code == 200


@pytest.mark.django_db
def test_genuine_cross_origin_cannot_use_same_origin_fetch_evidence():
    with override_settings(**_SCOPED_SETTINGS):
        client = Client(enforce_csrf_checks=True)
        csrf = client.get("/csrf/", secure=True).json()["csrf_token"]
        response = client.post(
            "/d1-research/lab/start", data="{}",
            content_type="application/json", secure=True,
            HTTP_X_CSRFTOKEN=csrf,
            HTTP_ORIGIN="https://evil.example",
            HTTP_SEC_FETCH_SITE="same-origin",
            HTTP_SEC_FETCH_MODE="cors",
        )
        assert response.status_code == 403


@pytest.mark.django_db
def test_null_origin_rejected_on_nonlaboratory_endpoints():
    with override_settings(**_SCOPED_SETTINGS):
        client = Client(enforce_csrf_checks=True)
        csrf = client.get("/csrf/", secure=True).json()["csrf_token"]
        response = client.post(
            "/not-a-lab-endpoint", data="{}",
            content_type="application/json", secure=True,
            HTTP_X_CSRFTOKEN=csrf, HTTP_ORIGIN="null",
            HTTP_SEC_FETCH_SITE="same-origin",
            HTTP_SEC_FETCH_MODE="cors",
        )
        assert response.status_code in (403, 404)
