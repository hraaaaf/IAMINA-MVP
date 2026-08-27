"""Public pilot app/API compatibility endpoint."""
from __future__ import annotations

from ninja import Router, Schema
from ninja.errors import HttpError

from core.app_compatibility import (
    API_CONTRACT_VERSION,
    CompatibilityConfigurationError,
    InvalidClientVersion,
    evaluate_client_compatibility,
    load_compatibility_policy,
)

router = Router()


class AppCompatibilitySchema(Schema):
    api_contract_version: str
    minimum_supported_app_version: str
    minimum_supported_build: int
    latest_app_version: str
    latest_build: int
    client_app_version: str | None
    client_build: int | None
    status: str
    compatible: bool | None
    update_required: bool
    update_available: bool


@router.get(
    "/app-compatibility",
    auth=None,
    tags=["ops"],
    response=AppCompatibilitySchema,
)
def app_compatibility(
    request,
    client_version: str | None = None,
    client_build: int | None = None,
):
    """Return the current pilot compatibility window and client decision."""
    try:
        policy = load_compatibility_policy()
        decision = evaluate_client_compatibility(
            client_version=client_version,
            client_build=client_build,
            policy=policy,
        )
    except InvalidClientVersion as exc:
        raise HttpError(422, str(exc)) from exc
    except CompatibilityConfigurationError as exc:
        raise HttpError(503, "app compatibility policy unavailable") from exc

    return {
        "api_contract_version": API_CONTRACT_VERSION,
        "minimum_supported_app_version": policy.minimum_version_text,
        "minimum_supported_build": policy.minimum.build,
        "latest_app_version": policy.latest_version_text,
        "latest_build": policy.latest.build,
        "client_app_version": client_version,
        "client_build": client_build,
        "status": decision.status,
        "compatible": decision.compatible,
        "update_required": decision.update_required,
        "update_available": decision.update_available,
    }
