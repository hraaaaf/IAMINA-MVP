"""
core.api.v1.dependencies — Reusable Django Ninja dependency factories.

Usage in a router endpoint:
    from core.api.v1.dependencies import require_module

    @router.get("/logs")
    def logs(request: HttpRequest, _: PatientModule = Depends(require_module("diabetes"))):
        ...
"""
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from core.models.patient import BasePatientProfile
from core.models.patient_module import PatientModule


def require_module(module_name: str):
    """Dependency factory — raises HttpError(404) if patient has not activated *module_name*."""

    def dependency(request: HttpRequest) -> PatientModule:
        base = get_object_or_404(BasePatientProfile, patient=request.user)
        pm = PatientModule.objects.filter(
            patient=base, module_name=module_name, is_active=True
        ).first()
        if pm is None:
            raise HttpError(404, f"Module '{module_name}' not activated for this patient")
        return pm

    return dependency
