"""
core.api.v1.modules — Per-patient module activation endpoints.

POST /api/v1/account/modules/{module_name}/activate
GET  /api/v1/account/modules
"""
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from core.models.patient import BasePatientProfile
from core.models.patient_module import PatientModule
from core.registry import ModuleRegistry

router = Router(tags=["modules"])


@router.post("/account/modules/{module_name}/activate")
def activate_module(request: HttpRequest, module_name: str):
    """Enrol the authenticated patient into *module_name*.

    Returns 404 if the module is not registered with the chassis ModuleRegistry.
    Idempotent — calling twice does not create a duplicate row.
    """
    if not ModuleRegistry.is_registered(module_name):
        raise HttpError(404, f"Module '{module_name}' is not registered")
    base = get_object_or_404(BasePatientProfile, patient=request.user)
    pm, _created = PatientModule.objects.get_or_create(
        patient=base,
        module_name=module_name,
        defaults={"is_active": True},
    )
    if not pm.is_active:
        pm.is_active = True
        pm.save(update_fields=["is_active"])
    return {"module": module_name, "activated": True, "activated_at": pm.activated_at}


@router.get("/account/modules")
def list_modules(request: HttpRequest):
    """Return all modules currently active for the authenticated patient."""
    base = get_object_or_404(BasePatientProfile, patient=request.user)
    modules = PatientModule.objects.filter(patient=base, is_active=True)
    return {
        "modules": [
            {"name": m.module_name, "is_active": m.is_active, "activated_at": m.activated_at}
            for m in modules
        ]
    }
