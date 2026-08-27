"""Pilot app/API compatibility policy.

The contract is deliberately small and public: a client that supplies its
SemVer + monotonically increasing build number gets a deterministic update
state. A client that supplies no version metadata is reported as unknown, never
falsely labelled compatible.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Mapping

_STABLE_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

DEFAULT_MIN_SUPPORTED_VERSION = "0.1.0"
DEFAULT_MIN_SUPPORTED_BUILD = 1
DEFAULT_LATEST_VERSION = "0.1.0"
DEFAULT_LATEST_BUILD = 1
API_CONTRACT_VERSION = "1"


class CompatibilityConfigurationError(ValueError):
    """Raised when the server-side compatibility window is invalid."""


class InvalidClientVersion(ValueError):
    """Raised when supplied client version metadata is malformed."""


@dataclass(frozen=True, order=True, slots=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int


@dataclass(frozen=True, order=True, slots=True)
class VersionBuild:
    version: SemanticVersion
    build: int


@dataclass(frozen=True, slots=True)
class CompatibilityPolicy:
    minimum: VersionBuild
    latest: VersionBuild
    minimum_version_text: str
    latest_version_text: str


@dataclass(frozen=True, slots=True)
class CompatibilityDecision:
    status: str
    compatible: bool | None
    update_required: bool
    update_available: bool


def parse_stable_semver(value: str) -> SemanticVersion:
    match = _STABLE_SEMVER.fullmatch(value.strip())
    if match is None:
        raise ValueError("expected stable MAJOR.MINOR.PATCH SemVer")
    return SemanticVersion(*(int(part) for part in match.groups()))


def _parse_build(value: str | int, *, field: str) -> int:
    try:
        build = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if build < 1:
        raise ValueError(f"{field} must be a positive integer")
    return build


def load_compatibility_policy(
    env: Mapping[str, str] | None = None,
) -> CompatibilityPolicy:
    source = os.environ if env is None else env
    minimum_text = source.get(
        "PILOT_MIN_SUPPORTED_APP_VERSION",
        DEFAULT_MIN_SUPPORTED_VERSION,
    ).strip()
    latest_text = source.get(
        "PILOT_LATEST_APP_VERSION",
        DEFAULT_LATEST_VERSION,
    ).strip()
    try:
        minimum = VersionBuild(
            parse_stable_semver(minimum_text),
            _parse_build(
                source.get(
                    "PILOT_MIN_SUPPORTED_BUILD",
                    str(DEFAULT_MIN_SUPPORTED_BUILD),
                ),
                field="PILOT_MIN_SUPPORTED_BUILD",
            ),
        )
        latest = VersionBuild(
            parse_stable_semver(latest_text),
            _parse_build(
                source.get(
                    "PILOT_LATEST_BUILD",
                    str(DEFAULT_LATEST_BUILD),
                ),
                field="PILOT_LATEST_BUILD",
            ),
        )
    except ValueError as exc:
        raise CompatibilityConfigurationError(str(exc)) from exc
    if minimum > latest:
        raise CompatibilityConfigurationError(
            "minimum supported app version/build cannot exceed latest"
        )
    return CompatibilityPolicy(
        minimum=minimum,
        latest=latest,
        minimum_version_text=minimum_text,
        latest_version_text=latest_text,
    )


def evaluate_client_compatibility(
    *,
    client_version: str | None,
    client_build: int | None,
    policy: CompatibilityPolicy,
) -> CompatibilityDecision:
    if client_version is None or client_build is None:
        return CompatibilityDecision(
            status="version_unknown",
            compatible=None,
            update_required=False,
            update_available=False,
        )
    try:
        client = VersionBuild(
            parse_stable_semver(client_version),
            _parse_build(client_build, field="client_build"),
        )
    except ValueError as exc:
        raise InvalidClientVersion(str(exc)) from exc

    if client < policy.minimum:
        return CompatibilityDecision(
            status="update_required",
            compatible=False,
            update_required=True,
            update_available=True,
        )
    if client < policy.latest:
        return CompatibilityDecision(
            status="update_available",
            compatible=True,
            update_required=False,
            update_available=True,
        )
    if client == policy.latest:
        return CompatibilityDecision(
            status="current",
            compatible=True,
            update_required=False,
            update_available=False,
        )
    return CompatibilityDecision(
        status="client_ahead",
        compatible=None,
        update_required=False,
        update_available=False,
    )
