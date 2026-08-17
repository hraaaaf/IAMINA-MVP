from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Literal

from django.db import transaction
from django.utils import timezone
from ninja import Router, Schema
from ninja.errors import HttpError

from diabetes.models.cgm import CGMConnection, CGMReadingRecord
from diabetes.services.cgm_credentials import CGMCredentialError, encrypt_cgm_credential
from diabetes.services.cgm_network import validate_patient_cgm_base_url
from diabetes.services.cgm_sync import CGMSyncError, sync_patient_cgm
from integrations.cgm import CGMSource, NightscoutConfig

router = Router(tags=["cgm"])


class CGMConnectionInput(Schema):
    source: Literal["dexcom", "libre", "linx"]
    base_url: str
    auth_type: Literal["bearer", "api_secret"]
    credential: str


class CGMConnectionResponse(Schema):
    connected: bool
    source: str | None = None
    base_url: str | None = None
    auth_type: str | None = None
    credential_set: bool = False
    enabled: bool = False
    last_sync_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error_code: str = ""


class CGMReadingResponse(Schema):
    recorded_at: datetime
    glucose_mg_dl: int
    trend: str
    device: str
    source: str


class CGMSyncResponse(Schema):
    received: int
    inserted: int
    last_recorded_at: datetime | None = None


def _connection_response(connection: CGMConnection | None) -> dict:
    if connection is None:
        return {"connected": False}
    return {
        "connected": True,
        "source": connection.source,
        "base_url": connection.base_url,
        "auth_type": connection.auth_type,
        "credential_set": bool(connection.encrypted_credential),
        "enabled": connection.enabled,
        "last_sync_at": connection.last_sync_at,
        "last_success_at": connection.last_success_at,
        "last_error_code": connection.last_error_code,
    }


@router.get("/cgm/connection", response=CGMConnectionResponse)
def get_cgm_connection(request):
    connection = CGMConnection.objects.filter(patient=request.user).first()
    return _connection_response(connection)


@router.put("/cgm/connection", response=CGMConnectionResponse)
def put_cgm_connection(request, payload: CGMConnectionInput):
    credential = payload.credential.strip()
    if not credential or len(credential) > 4096:
        raise HttpError(422, "Invalid CGM credential")

    try:
        base_url = validate_patient_cgm_base_url(payload.base_url)
        if payload.auth_type == CGMConnection.AuthType.BEARER:
            stored_credential = credential
            auth_kwargs = {"bearer_token": stored_credential}
        else:
            # Nightscout v1 requires SHA-1 for this protocol field. This is not
            # a security hash: the raw patient-entered secret is transformed
            # before encrypted persistence and never needs to be recovered.
            stored_credential = hashlib.sha1(
                credential.encode("utf-8"), usedforsecurity=False
            ).hexdigest()
            auth_kwargs = {"api_secret_sha1": stored_credential}

        NightscoutConfig(
            base_url=base_url,
            source=CGMSource(payload.source),
            **auth_kwargs,
        )
        encrypted = encrypt_cgm_credential(stored_credential)
    except (ValueError, CGMCredentialError) as exc:
        code = str(exc)
        status = 503 if code.startswith("cgm_credential_key_") else 422
        raise HttpError(status, code) from exc

    with transaction.atomic():
        connection, _ = CGMConnection.objects.update_or_create(
            patient=request.user,
            defaults={
                "source": payload.source,
                "base_url": base_url,
                "auth_type": payload.auth_type,
                "encrypted_credential": encrypted,
                "enabled": True,
                "last_sync_at": None,
                "last_success_at": None,
                "last_error_code": "",
            },
        )
    return _connection_response(connection)


@router.delete("/cgm/connection", response={204: None})
def delete_cgm_connection(request):
    CGMConnection.objects.filter(patient=request.user).delete()
    return 204, None


@router.post("/cgm/sync", response=CGMSyncResponse)
def sync_cgm(request):
    try:
        result = sync_patient_cgm(patient_id=request.user.id)
    except CGMSyncError as exc:
        code = str(exc)
        status = 503 if code in {
            "cgm_credential_key_unavailable",
            "cgm_credential_key_invalid",
            "cgm_credential_unreadable",
            "provider_unavailable",
            "cgm_bridge_host_unresolvable",
        } else 409
        raise HttpError(status, code) from exc
    return {
        "received": result.received,
        "inserted": result.inserted,
        "last_recorded_at": result.last_recorded_at,
    }


@router.get("/cgm/readings", response=list[CGMReadingResponse])
def list_cgm_readings(request, hours: int = 24):
    hours = max(1, min(hours, 24 * 7))
    since = timezone.now() - timedelta(hours=hours)
    rows = CGMReadingRecord.objects.filter(
        patient=request.user,
        recorded_at__gte=since,
    ).order_by("recorded_at")
    return [
        {
            "recorded_at": row.recorded_at,
            "glucose_mg_dl": row.glucose_mg_dl,
            "trend": row.trend,
            "device": row.device,
            "source": row.source,
        }
        for row in rows
    ]
