from __future__ import annotations

import pytest
from django.conf import settings
from django.test import RequestFactory
from ninja.errors import HttpError

from amina.vercel_session_auth import SessionAuth

OBSERVED_FRONTEND_ORIGIN = (
    "https://iamina-review-irpy8kz09-achraf-benmoussa-s-projects.vercel.app"
)


def _post(origin: str):
    request = RequestFactory().post(
        "/api/v1/account/consent",
        HTTP_ORIGIN=origin,
        HTTP_X_CSRFTOKEN="a" * 32,
    )
    request.COOKIES["csrftoken"] = "a" * 32
    request.COOKIES[settings.SESSION_COOKIE_NAME] = "session-key"
    return request


def test_observed_vercel_origin_passes_ninja_session_csrf_check() -> None:
    auth = SessionAuth()

    assert auth._get_key(_post(OBSERVED_FRONTEND_ORIGIN)) == "session-key"


def test_unrelated_vercel_origin_is_rejected_by_ninja_session_csrf_check() -> None:
    auth = SessionAuth()

    with pytest.raises(HttpError) as exc:
        auth._get_key(_post("https://other-app.vercel.app"))

    assert exc.value.status_code == 403
