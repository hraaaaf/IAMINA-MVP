"""CAL-12 fixture HTTP must be unavailable under ordinary production URLConf."""
import pytest
from django.test import RequestFactory
from django.urls import Resolver404, resolve


def test_cal12_fixture_paths_do_not_exist_in_main_urlconf():
    for path in (
        "/_cal12_fixture/",
        "/_cal12_fixture/grant",
        "/_cal12_fixture/check",
        "/_cal12_fixture/revoke",
    ):
        with pytest.raises(Resolver404):
            resolve(path, urlconf="amina.urls")


def test_cal12_fixture_html_returns_403_without_explicit_test_gate(
    settings, monkeypatch,
):
    from core.tests.cal12_fue_urls import index

    monkeypatch.delenv("CAL12_FUE_TEST_ONLY", raising=False)
    settings.CAL12_SYNTHETIC_EXPORT_LEDGER_ENABLED = False
    request = RequestFactory().get(
        "/_cal12_fixture/", HTTP_HOST="127.0.0.1:8000",
    )
    request.META["REMOTE_ADDR"] = "127.0.0.1"
    assert index(request).status_code == 403


def test_cal12_fixture_html_rejects_non_loopback_request(settings, monkeypatch):
    from core.tests.cal12_fue_urls import index

    monkeypatch.setenv("CAL12_FUE_TEST_ONLY", "1")
    settings.CAL12_SYNTHETIC_EXPORT_LEDGER_ENABLED = True
    request = RequestFactory().get(
        "/_cal12_fixture/", HTTP_HOST="localhost:8000",
    )
    request.META["REMOTE_ADDR"] = "127.0.0.1"
    assert index(request).status_code == 403
