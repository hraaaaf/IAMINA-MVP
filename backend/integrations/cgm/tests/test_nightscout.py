from __future__ import annotations

from datetime import UTC, datetime

import pytest

from integrations.cgm import CGMSource, NightscoutCGMProvider, NightscoutConfig
from integrations.cgm.nightscout import CGMProviderError


def test_normalizes_and_sorts_valid_readings() -> None:
    seen: dict[str, object] = {}

    def transport(url: str, headers: dict[str, str], timeout: float) -> object:
        seen.update(url=url, headers=headers, timeout=timeout)
        return [
            {"sgv": 140, "date": 1_768_176_120_000, "direction": "Flat", "device": "bridge"},
            {"sgv": 120, "date": 1_768_176_060_000, "direction": "FortyFiveUp"},
            {"sgv": 0, "date": 1_768_176_180_000},
            {"sgv": "130", "date": 1_768_176_180_000},
        ]

    provider = NightscoutCGMProvider(
        NightscoutConfig(
            base_url="https://example.invalid",
            source=CGMSource.DEXCOM,
            bearer_token="test-token",
        ),
        transport=transport,
    )

    readings = provider.readings(datetime(2026, 1, 11, 23, 59, tzinfo=UTC))

    assert [reading.glucose_mg_dl for reading in readings] == [120, 140]
    assert all(reading.source is CGMSource.DEXCOM for reading in readings)
    assert readings[0].trend == "FortyFiveUp"
    assert readings[1].device == "bridge"
    assert "find%5Bdate%5D%5B%24gte%5D=" in str(seen["url"])
    assert seen["headers"] == {"Accept": "application/json", "Authorization": "Bearer test-token"}


def test_libre_source_is_explicit_not_inferred_from_device_text() -> None:
    def transport(url: str, headers: dict[str, str], timeout: float) -> object:
        return [{"sgv": 101, "date": 1_768_176_120_000, "device": "looks-like-dexcom"}]

    provider = NightscoutCGMProvider(
        NightscoutConfig(base_url="https://example.invalid", source=CGMSource.LIBRE),
        transport=transport,
    )

    [reading] = provider.readings(datetime(2026, 1, 11, 23, 59, tzinfo=UTC))
    assert reading.source is CGMSource.LIBRE


def test_rejects_insecure_remote_url_and_ambiguous_auth() -> None:
    for unsafe_url in (
        "http://example.com",
        "http://localhost.evil.example",
        "http://127.0.0.1.evil.example",
        "https://user:password@example.com",
    ):
        with pytest.raises(ValueError):
            NightscoutConfig(base_url=unsafe_url, source=CGMSource.DEXCOM)

    with pytest.raises(ValueError):
        NightscoutConfig(
            base_url="https://example.com",
            source=CGMSource.DEXCOM,
            bearer_token="a",
            api_secret_sha1="b",
        )

    with pytest.raises(ValueError):
        NightscoutConfig(base_url="https://example.com", source=CGMSource.DEXCOM, timeout_seconds=0)

    NightscoutConfig(base_url="http://localhost:1337", source=CGMSource.DEXCOM)
    NightscoutConfig(base_url="http://127.0.0.1:1337", source=CGMSource.LIBRE)


def test_rejects_naive_since_and_invalid_payload() -> None:
    provider = NightscoutCGMProvider(
        NightscoutConfig(base_url="https://example.invalid", source=CGMSource.DEXCOM),
        transport=lambda *_: {"not": "a list"},
    )

    with pytest.raises(ValueError):
        provider.readings(datetime(2026, 1, 1))

    with pytest.raises(CGMProviderError):
        provider.readings(datetime(2026, 1, 1, tzinfo=UTC))


def test_health_fails_closed_without_leaking_provider_error() -> None:
    def failing_transport(url: str, headers: dict[str, str], timeout: float) -> object:
        raise CGMProviderError("secret upstream detail")

    provider = NightscoutCGMProvider(
        NightscoutConfig(base_url="https://example.invalid", source=CGMSource.LIBRE),
        transport=failing_transport,
    )

    health = provider.health()
    assert health.ok is False
    assert health.detail == "provider_unavailable"
