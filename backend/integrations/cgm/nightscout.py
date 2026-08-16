from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from typing import Callable
from urllib.parse import urlencode, urljoin, urlparse

from .contracts import CGMProvider, CGMReading, CGMSource, ProviderHealth


class CGMProviderError(RuntimeError):
    """Provider boundary failure with no secret-bearing detail."""


@dataclass(frozen=True, slots=True)
class NightscoutConfig:
    base_url: str
    source: CGMSource
    bearer_token: str | None = None
    api_secret_sha1: str | None = None
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        if self.source not in {CGMSource.DEXCOM, CGMSource.LIBRE}:
            raise ValueError("CGM V1 supports only Dexcom or Libre source provenance")

        parsed = urlparse(self.base_url)
        is_loopback_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" and not is_loopback_http:
            raise ValueError("Nightscout base_url must use HTTPS outside localhost")
        if not parsed.hostname:
            raise ValueError("Nightscout base_url must contain a hostname")
        if parsed.username or parsed.password:
            raise ValueError("Nightscout credentials must not be embedded in the URL")
        if self.bearer_token and self.api_secret_sha1:
            raise ValueError("Configure one Nightscout authentication method only")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


Transport = Callable[[str, dict[str, str], float], object]


def _stdlib_transport(url: str, headers: dict[str, str], timeout: float) -> object:
    """Issue one GET request using only HTTPS or exact loopback HTTP."""

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise CGMProviderError("CGM provider request failed")

        if parsed.scheme == "https":
            connection: HTTPConnection = HTTPSConnection(hostname, parsed.port, timeout=timeout)
        elif parsed.scheme == "http" and hostname in {"localhost", "127.0.0.1", "::1"}:
            connection = HTTPConnection(hostname, parsed.port, timeout=timeout)
        else:
            raise CGMProviderError("CGM provider request failed")

        target = parsed.path or "/"
        if parsed.query:
            target = f"{target}?{parsed.query}"

        try:
            connection.request("GET", target, headers=headers)
            response = connection.getresponse()
            if not 200 <= response.status < 300:
                raise CGMProviderError("CGM provider request failed")
            return json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()
    except CGMProviderError:
        raise
    except (HTTPException, OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        raise CGMProviderError("CGM provider request failed") from exc


class NightscoutCGMProvider(CGMProvider):
    """Read normalized CGM entries from a Nightscout-compatible API.

    Dexcom Share and LibreLinkUp credentials stay in the external bridge
    (for example nightscout-connect/Nightscout). IAMINA receives only the
    normalized glucose feed and configured source provenance.
    """

    def __init__(self, config: NightscoutConfig, *, transport: Transport | None = None) -> None:
        self._config = config
        self._transport = transport or _stdlib_transport

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._config.bearer_token:
            headers["Authorization"] = f"Bearer {self._config.bearer_token}"
        elif self._config.api_secret_sha1:
            headers["api-secret"] = self._config.api_secret_sha1
        return headers

    def _url(self, since: datetime) -> str:
        if since.tzinfo is None:
            raise ValueError("since must be timezone-aware")
        params = urlencode({"find[date][$gte]": int(since.timestamp() * 1000), "count": 1000})
        base = self._config.base_url.rstrip("/") + "/"
        return f"{urljoin(base, 'api/v1/entries.json')}?{params}"

    def readings(self, since: datetime) -> list[CGMReading]:
        payload = self._transport(self._url(since), self._headers(), self._config.timeout_seconds)
        if not isinstance(payload, list):
            raise CGMProviderError("CGM provider returned an invalid payload")

        readings: list[CGMReading] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            glucose = item.get("sgv")
            epoch_ms = item.get("date")
            if not isinstance(glucose, int) or isinstance(glucose, bool) or glucose <= 0:
                continue
            if not isinstance(epoch_ms, (int, float)) or isinstance(epoch_ms, bool) or epoch_ms <= 0:
                continue

            timestamp = datetime.fromtimestamp(epoch_ms / 1000, tz=UTC)
            if timestamp < since.astimezone(UTC):
                continue

            trend = item.get("direction") if isinstance(item.get("direction"), str) else None
            device = item.get("device") if isinstance(item.get("device"), str) else None
            readings.append(
                CGMReading(
                    timestamp=timestamp,
                    glucose_mg_dl=glucose,
                    source=self._config.source,
                    trend=trend,
                    device=device,
                )
            )

        readings.sort(key=lambda reading: reading.timestamp)
        return readings

    def health(self) -> ProviderHealth:
        checked_at = datetime.now(tz=UTC)
        try:
            probe_since = checked_at.replace(microsecond=0)
            self._transport(self._url(probe_since), self._headers(), self._config.timeout_seconds)
        except (CGMProviderError, ValueError, TypeError):
            return ProviderHealth(ok=False, checked_at=checked_at, detail="provider_unavailable")
        return ProviderHealth(ok=True, checked_at=checked_at)
