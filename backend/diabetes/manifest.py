"""
DIABETES_MANIFEST — frozen ModuleManifest for the Diabetes Companion module.

Registered with ModuleRegistry in DiabetesConfig.ready().
"""
from core.contracts.manifest import ModuleManifest

DIABETES_MANIFEST = ModuleManifest(
    name="diabetes",
    version="1.0.0",
    condition="E11",
    url_prefix="/diabetes",
    tags=["diabetes"],
    supported_languages=["fr", "ar-MA", "ar"],
    interactive_endpoints=["/api/v1/diabetes/ai/chat"],
    acquisition_event="log_created",
)
