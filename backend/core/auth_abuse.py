"""Database-backed abuse protection for public authentication endpoints."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import math
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models import AuthAbuseBucket


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    limit: int
    window_seconds: int


_DEFAULT_RULES = {
    "login_ip": RateLimitRule(limit=20, window_seconds=600),
    "login_account": RateLimitRule(limit=10, window_seconds=600),
    "register_ip": RateLimitRule(limit=10, window_seconds=3600),
    "register_account": RateLimitRule(limit=5, window_seconds=3600),
    "password_reset_ip": RateLimitRule(limit=10, window_seconds=3600),
    "password_reset_account": RateLimitRule(limit=5, window_seconds=3600),
}
_ACTION_SCOPES = {
    "login": ("login_ip", "login_account"),
    "register": ("register_ip", "register_account"),
    "password_reset": ("password_reset_ip", "password_reset_account"),
}


class AuthRateLimitExceeded(RuntimeError):
    def __init__(self, retry_after: int):
        super().__init__("auth_rate_limited")
        self.retry_after = max(1, int(retry_after))


def _configured_rule(scope: str) -> RateLimitRule:
    default = _DEFAULT_RULES[scope]
    overrides = getattr(settings, "AUTH_ABUSE_LIMITS", {}) or {}
    raw = overrides.get(scope)
    if raw is None:
        return default
    if isinstance(raw, dict):
        limit = int(raw.get("limit", default.limit))
        window_seconds = int(raw.get("window_seconds", default.window_seconds))
    elif isinstance(raw, (tuple, list)) and len(raw) == 2:
        limit, window_seconds = map(int, raw)
    else:
        raise ValueError(f"Invalid AUTH_ABUSE_LIMITS rule for {scope}")
    if limit <= 0 or window_seconds <= 0:
        raise ValueError(f"AUTH_ABUSE_LIMITS values must be positive for {scope}")
    return RateLimitRule(limit=limit, window_seconds=window_seconds)


def _hash_identifier(kind: str, value: str) -> str:
    secret = settings.SECRET_KEY.encode("utf-8")
    payload = f"auth-abuse:v1:{kind}:{value}".encode("utf-8")
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def _client_ip(request) -> str:
    if request is None:
        return "unknown"
    meta = getattr(request, "META", {}) or {}
    forwarded = str(meta.get("HTTP_X_FORWARDED_FOR", "")).split(",", 1)[0].strip()
    remote = str(meta.get("REMOTE_ADDR", "")).strip()
    for candidate in (forwarded, remote):
        if not candidate:
            continue
        try:
            return ipaddress.ip_address(candidate).compressed
        except ValueError:
            continue
    return "unknown"


def _normalize_identity(identity: str | None) -> str | None:
    if not isinstance(identity, str):
        return None
    normalized = identity.strip().lower()
    if not normalized or len(normalized) > 254:
        return None
    return normalized


@transaction.atomic
def _consume(scope: str, key_hash: str, *, now) -> None:
    rule = _configured_rule(scope)
    bucket, _ = AuthAbuseBucket.objects.select_for_update().get_or_create(
        scope=scope,
        key_hash=key_hash,
        defaults={"window_started_at": now, "count": 0},
    )
    window_end = bucket.window_started_at + timedelta(seconds=rule.window_seconds)
    if now >= window_end:
        bucket.window_started_at = now
        bucket.count = 0
        window_end = now + timedelta(seconds=rule.window_seconds)

    if bucket.count >= rule.limit:
        retry_after = math.ceil((window_end - now).total_seconds())
        raise AuthRateLimitExceeded(retry_after)

    bucket.count += 1
    bucket.save(update_fields=("count", "window_started_at", "updated_at"))


def enforce_auth_abuse_limit(request, action: str, *, identity: str | None = None) -> None:
    """Consume the persistent buckets for one authentication operation."""
    try:
        ip_scope, account_scope = _ACTION_SCOPES[action]
    except KeyError as exc:
        raise ValueError(f"Unknown auth abuse action: {action}") from exc

    now = timezone.now()
    client_ip = _client_ip(request)
    _consume(ip_scope, _hash_identifier("ip", client_ip), now=now)

    normalized_identity = _normalize_identity(identity)
    if normalized_identity is not None:
        _consume(
            account_scope,
            _hash_identifier("account", normalized_identity),
            now=now,
        )
