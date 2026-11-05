"""W01/G7: anonymous HTTP requests must not reach protected clinical routers.

Django Ninja can apply auth at the add_router() mount without modifying the
unbound Router template. Verify actual requests, not template auth_callbacks.
This checks a representative operation per explicitly protected router.
"""

import json

import pytest
from django.test import Client


PROTECTED_HTTP_ROUTES = (
    ("GET", "/api/v1/logs"),
    ("GET", "/api/v1/profile"),
    ("GET", "/api/v1/profile/locale"),
    ("GET", "/api/v1/kpis/"),
    ("GET", "/api/v1/personal-response/"),
    ("GET", "/api/v1/proactive-insights/preview/"),
    ("GET", "/api/v1/companion/overview"),
    ("GET", "/api/v1/cgm/connection"),
    ("GET", "/api/v1/account/consent"),
    ("GET", "/api/v1/account/modules"),
    ("POST", "/api/v1/import/librelink"),
    ("GET", "/api/v1/documents/"),
    ("GET", "/api/v1/ai/doctor-brief"),
    ("POST", "/api/v1/ai/voice"),
    ("GET", "/api/v1/analytics/overview"),
)


@pytest.mark.django_db
@pytest.mark.parametrize(("method", "path"), PROTECTED_HTTP_ROUTES)
def test_anonymous_cannot_access_protected_routes(method, path):
    client = Client()
    if method == "GET":
        response = client.get(path)
    else:
        response = client.post(path, data=json.dumps({}), content_type="application/json")
    assert response.status_code in (401, 403), (
        f"Protected route {method} {path}: "
        f"expected 401/403, got {response.status_code}"
    )


@pytest.mark.django_db
@pytest.mark.parametrize("path", (
    "/api/v1/profile",
    "/api/v1/kpis/",
    "/api/v1/account/consent",
    "/api/v1/documents/",
))
def test_invalid_bearer_is_not_accepted_by_protected_routes(path):
    response = Client().get(path, HTTP_AUTHORIZATION="Bearer invalid-w01")
    assert response.status_code in (401, 403), (
        f"Invalid bearer reached {path}: HTTP {response.status_code}"
    )
