from types import SimpleNamespace

import pytest
from ninja.errors import HttpError

from core.api.v1.compatibility import app_compatibility
from core.app_compatibility import (
    CompatibilityConfigurationError,
    InvalidClientVersion,
    evaluate_client_compatibility,
    load_compatibility_policy,
)


def _policy(**overrides):
    env = {
        "PILOT_MIN_SUPPORTED_APP_VERSION": "0.1.0",
        "PILOT_MIN_SUPPORTED_BUILD": "5",
        "PILOT_LATEST_APP_VERSION": "0.2.0",
        "PILOT_LATEST_BUILD": "9",
    }
    env.update(overrides)
    return load_compatibility_policy(env)


def test_missing_client_metadata_is_unknown_not_falsely_compatible():
    decision = evaluate_client_compatibility(
        client_version=None,
        client_build=None,
        policy=_policy(),
    )

    assert decision.status == "version_unknown"
    assert decision.compatible is None
    assert decision.update_required is False


def test_below_minimum_version_requires_update():
    decision = evaluate_client_compatibility(
        client_version="0.0.9",
        client_build=99,
        policy=_policy(),
    )

    assert decision.status == "update_required"
    assert decision.compatible is False
    assert decision.update_required is True


def test_same_version_below_minimum_build_requires_update():
    decision = evaluate_client_compatibility(
        client_version="0.1.0",
        client_build=4,
        policy=_policy(),
    )

    assert decision.status == "update_required"
    assert decision.update_required is True


def test_supported_older_client_gets_non_blocking_update_available():
    decision = evaluate_client_compatibility(
        client_version="0.1.0",
        client_build=5,
        policy=_policy(),
    )

    assert decision.status == "update_available"
    assert decision.compatible is True
    assert decision.update_required is False
    assert decision.update_available is True


def test_latest_is_compatible_but_client_ahead_is_unknown():
    current = evaluate_client_compatibility(
        client_version="0.2.0",
        client_build=9,
        policy=_policy(),
    )
    ahead = evaluate_client_compatibility(
        client_version="0.3.0",
        client_build=1,
        policy=_policy(),
    )

    assert current.status == "current"
    assert current.compatible is True
    assert ahead.status == "client_ahead"
    assert ahead.compatible is None
    assert ahead.update_required is False


def test_invalid_client_version_is_rejected():
    with pytest.raises(InvalidClientVersion):
        evaluate_client_compatibility(
            client_version="v0.1",
            client_build=1,
            policy=_policy(),
        )


def test_invalid_server_window_fails_closed():
    with pytest.raises(CompatibilityConfigurationError):
        _policy(
            PILOT_MIN_SUPPORTED_APP_VERSION="0.3.0",
            PILOT_LATEST_APP_VERSION="0.2.0",
        )


def test_public_endpoint_exposes_update_required_state(monkeypatch):
    monkeypatch.setenv("PILOT_MIN_SUPPORTED_APP_VERSION", "0.1.0")
    monkeypatch.setenv("PILOT_MIN_SUPPORTED_BUILD", "5")
    monkeypatch.setenv("PILOT_LATEST_APP_VERSION", "0.2.0")
    monkeypatch.setenv("PILOT_LATEST_BUILD", "9")

    payload = app_compatibility(
        SimpleNamespace(),
        client_version="0.1.0",
        client_build=4,
    )

    assert payload["api_contract_version"] == "1"
    assert payload["minimum_supported_app_version"] == "0.1.0"
    assert payload["minimum_supported_build"] == 5
    assert payload["status"] == "update_required"
    assert payload["update_required"] is True


def test_public_endpoint_maps_invalid_client_metadata_to_422(monkeypatch):
    monkeypatch.setenv("PILOT_MIN_SUPPORTED_APP_VERSION", "0.1.0")
    monkeypatch.setenv("PILOT_MIN_SUPPORTED_BUILD", "1")
    monkeypatch.setenv("PILOT_LATEST_APP_VERSION", "0.1.0")
    monkeypatch.setenv("PILOT_LATEST_BUILD", "1")

    with pytest.raises(HttpError) as exc_info:
        app_compatibility(
            SimpleNamespace(),
            client_version="bad",
            client_build=1,
        )

    assert exc_info.value.status_code == 422
