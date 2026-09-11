"""Exact release-SHA binding for real-patient pilot audit evidence."""

from __future__ import annotations

import re

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def require_expected_source_commit_sha(value: str | None) -> str:
    """Return a normalized full Git SHA or fail closed."""
    candidate = (value or "").strip().lower()
    if not candidate:
        raise ValueError(
            "exact candidate source commit SHA is required for an approved real-patient audit"
        )
    if not _SHA_RE.fullmatch(candidate):
        raise ValueError("expected source commit SHA must be a full 40-character Git SHA")
    return candidate


def bind_payload_to_expected_source_commit(
    payload: dict[str, object],
    *,
    expected_source_commit_sha: str,
    require_manifest_match: bool,
) -> dict[str, object]:
    """Bind retained audit output to one candidate SHA and optionally its manifest SHA."""
    expected = require_expected_source_commit_sha(expected_source_commit_sha)
    manifest_sha = str(payload.get("source_commit_sha") or "").strip().lower()
    if require_manifest_match:
        if not manifest_sha:
            raise ValueError("approved audit payload is missing source_commit_sha")
        if manifest_sha != expected:
            raise ValueError(
                "approved audit manifest source_commit_sha does not match the expected candidate SHA"
            )
    bound = dict(payload)
    bound["audited_source_commit_sha"] = expected
    return bound
