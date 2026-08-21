"""
LLM Rate Guard — Gemini free-tier daily cap enforcement.

Gemini free tier: 20 req/day (Flash-Lite).
Counter key: iamina:gemini:calls:{YYYY-MM-DD}  (Django cache, TTL = 25h)
Warning threshold: 18 calls; hard cap: 20 calls → local QuotaExhaustedProvider.

Failure modes handled:
  - Counter reaches warning threshold → WARNING; Gemini remains available.
  - Counter reaches hard cap → local quota response (no network failover).
  - Gemini returns a real 429 (API quota hit before local counter) →
    counter is fast-forwarded to _DAILY_LIMIT so all subsequent calls
    skip Gemini immediately; QuotaExhaustedProvider response is returned
    directly (previously fell through to the TIR-based _fallback_reply).
  - Redis unavailable (IGNORE_EXCEPTIONS=True silences cache errors) →
    module-level in-process dict acts as fallback counter so the cap is
    still enforced within the same process lifetime.
"""
import logging
import threading
from datetime import date

from django.core.cache import cache

from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)

_DAILY_LIMIT = 20
_WARN_THRESHOLD = 18
_COUNTER_TTL = 25 * 3600  # 25h — survives midnight rollover by 1h

# ── In-process fallback counter ────────────────────────────────────────────
# When Redis is unavailable (IGNORE_EXCEPTIONS=True makes cache ops silently
# return None), this dict keeps the count alive for the process lifetime.
# Format: {date_str: int}   e.g. {"2026-05-27": 5}
_local_counts: dict = {}
_local_lock = threading.Lock()


def _counter_key() -> str:
    return f"iamina:gemini:calls:{date.today().isoformat()}"


def _get_count() -> int:
    cached = cache.get(_counter_key())
    if cached is not None:
        return int(cached)
    # Redis unavailable or key missing — check in-process fallback
    with _local_lock:
        return _local_counts.get(date.today().isoformat(), 0)


def _increment() -> int:
    """Atomically increment and return the new count."""
    key = _counter_key()
    today = date.today().isoformat()
    try:
        new = cache.incr(key)
    except ValueError:
        # Key doesn't exist yet — set it to 1
        cache.set(key, 1, timeout=_COUNTER_TTL)
        new = 1

    # cache.incr returns None when Redis is down (IGNORE_EXCEPTIONS=True)
    if new is None:
        with _local_lock:
            _local_counts[today] = _local_counts.get(today, 0) + 1
            new = _local_counts[today]
    else:
        # Keep local in sync so a Redis restart doesn't reset the cap
        with _local_lock:
            _local_counts[today] = int(new)

    return new


def _mark_cap_reached() -> None:
    """Fast-forward the counter to the daily limit (used after a real 429)."""
    today = date.today().isoformat()
    cache.set(_counter_key(), _DAILY_LIMIT, timeout=_COUNTER_TTL)
    with _local_lock:
        _local_counts[today] = _DAILY_LIMIT


def _clear_local_count() -> None:
    """Reset the in-process fallback counter for today. Used in tests only."""
    with _local_lock:
        _local_counts.pop(date.today().isoformat(), None)


def _is_quota_error(exc: Exception) -> bool:
    """Return True for Gemini 429 / RESOURCE_EXHAUSTED responses."""
    s = str(exc)
    return "429" in s or "RESOURCE_EXHAUSTED" in s or "quota" in s.lower()


def should_use_gemini() -> bool:
    """Return True when Gemini quota is still available."""
    count = _get_count()
    if count >= _DAILY_LIMIT:
        logger.error(
            "Gemini daily cap reached (%d/%d). Failover active for the rest of the day.",
            count, _DAILY_LIMIT,
        )
        return False
    if count >= _WARN_THRESHOLD:
        logger.warning(
            "Gemini approaching daily cap (%d/%d). Local quota response will trigger at %d.",
            count, _DAILY_LIMIT, _DAILY_LIMIT,
        )
    return True


def record_gemini_call():
    """Call this after each successful Gemini request."""
    new = _increment()
    if new == _WARN_THRESHOLD:
        logger.warning(
            "Gemini daily cap warning: %d/%d calls used today.", new, _DAILY_LIMIT
        )
    elif new > _DAILY_LIMIT:
        logger.error(
            "Gemini over-cap: %d/%d — this call should not have reached Gemini.", new, _DAILY_LIMIT
        )


def _quota_exhausted_response(system: str, user: str) -> LLMResponse:
    """Return the proper QuotaExhaustedProvider message (imported lazily)."""
    from .fallback import QuotaExhaustedProvider
    return QuotaExhaustedProvider().complete(system, user)


def _quota_exhausted_stream(system: str, user: str):
    """Stream the QuotaExhaustedProvider message word by word."""
    from .fallback import QuotaExhaustedProvider
    yield from QuotaExhaustedProvider().stream(system, user)


# ──────────────────────────────────────────────────────────────
# Guarded provider wrapper
# ──────────────────────────────────────────────────────────────

class GuardedGeminiProvider(BaseLLMProvider):
    """
    Wraps GeminiProvider with daily-cap enforcement.

    Three outcomes:
      1. Counter below cap + Gemini succeeds → normal LLMResponse, counter++.
      2. Counter at/above cap (pre-checked) → returns QuotaExhaustedProvider.
      3. Gemini returns a real 429 → counter fast-forwarded to cap,
         QuotaExhaustedProvider response returned (no exception propagated).

    This ensures conversation.chat() NEVER sees a Gemini quota error —
    it always receives a clean LLMResponse, either real or degraded.
    """

    def __init__(self, inner: BaseLLMProvider):
        self._inner = inner

    @property
    def model_name(self) -> str:
        return getattr(self._inner, "model_name", "gemini-guarded")

    def complete(self, system: str, user: str) -> LLMResponse:
        if not should_use_gemini():
            return _quota_exhausted_response(system, user)
        try:
            result = self._inner.complete(system, user)
            record_gemini_call()
            return result
        except Exception as exc:
            if _is_quota_error(exc):
                _mark_cap_reached()
                logger.error(
                    "Gemini returned 429 — counter fast-forwarded to cap (%d). "
                    "Serving QuotaExhaustedProvider for the rest of the day.",
                    _DAILY_LIMIT,
                )
                return _quota_exhausted_response(system, user)
            raise

    def stream(self, system: str, user: str):
        if not should_use_gemini():
            yield from _quota_exhausted_stream(system, user)
            return
        try:
            result = self._inner.complete(system, user)
            record_gemini_call()
            words = result.content.split(" ")
            for i, word in enumerate(words):
                yield word if i == 0 else " " + word
        except Exception as exc:
            if _is_quota_error(exc):
                _mark_cap_reached()
                logger.error(
                    "Gemini returned 429 (stream) — counter fast-forwarded to cap (%d).",
                    _DAILY_LIMIT,
                )
                yield from _quota_exhausted_stream(system, user)
                return
            raise

    def think(self, system: str, user: str) -> tuple[str, str]:
        """
        Delegates think() to the inner provider with quota guard.
        Falls back gracefully — never raises.
        """
        if not should_use_gemini():
            return "", _quota_exhausted_response(system, user).content
        try:
            thinking, response = self._inner.think(system, user)
            record_gemini_call()
            return thinking, response
        except Exception as exc:
            if _is_quota_error(exc):
                _mark_cap_reached()
                logger.error(
                    "Gemini returned 429 (think) — counter fast-forwarded to cap (%d).",
                    _DAILY_LIMIT,
                )
                return "", _quota_exhausted_response(system, user).content
            # Non-quota error — fall back silently via base class default
            logger.debug("GuardedGeminiProvider.think: unexpected error, falling back.", exc_info=True)
            return "", ""
