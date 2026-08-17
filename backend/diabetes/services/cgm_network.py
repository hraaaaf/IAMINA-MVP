from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse


class CGMNetworkPolicyError(ValueError):
    """Patient-configured CGM bridge target is not eligible for server egress."""


def _allowed_hosts() -> set[str]:
    raw = os.environ.get("CGM_ALLOWED_BRIDGE_HOSTS", "")
    return {
        value.strip().rstrip(".").lower()
        for value in raw.split(",")
        if value.strip()
    }


def validate_patient_cgm_base_url(base_url: str) -> str:
    """Require an allowlisted public HTTPS Nightscout-compatible target.

    V1 permits exact loopback HTTP for developer-owned configuration. V2 accepts
    patient-controlled URLs, so its patient API is intentionally stricter: the
    hostname must be explicitly approved server-side, use HTTPS, and resolve only
    to globally routable addresses. The same policy is repeated at sync time.
    """

    normalized = base_url.strip().rstrip("/")
    parsed = urlparse(normalized)
    hostname = parsed.hostname
    if parsed.scheme != "https" or not hostname:
        raise CGMNetworkPolicyError("cgm_bridge_https_required")
    if parsed.username or parsed.password:
        raise CGMNetworkPolicyError("cgm_bridge_embedded_credentials_forbidden")

    lowered = hostname.rstrip(".").lower()
    if lowered == "localhost" or lowered.endswith(".localhost") or lowered.endswith(".local"):
        raise CGMNetworkPolicyError("cgm_bridge_host_not_public")

    try:
        literal = ipaddress.ip_address(lowered)
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        raise CGMNetworkPolicyError("cgm_bridge_host_not_public")

    allowed = _allowed_hosts()
    if not allowed:
        raise CGMNetworkPolicyError("cgm_bridge_allowlist_unconfigured")
    if lowered not in allowed:
        raise CGMNetworkPolicyError("cgm_bridge_host_not_allowed")

    try:
        resolved = socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise CGMNetworkPolicyError("cgm_bridge_host_unresolvable") from exc
    if not resolved:
        raise CGMNetworkPolicyError("cgm_bridge_host_unresolvable")

    for result in resolved:
        address = result[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise CGMNetworkPolicyError("cgm_bridge_host_unresolvable") from exc
        if not ip.is_global:
            raise CGMNetworkPolicyError("cgm_bridge_host_not_public")

    return normalized
