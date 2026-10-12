"""
DIABETES_MANIFEST — frozen ModuleManifest for the Diabetes Companion module.

Registered with ModuleRegistry in DiabetesConfig.ready().
"""
from core.contracts.manifest import ModuleManifest

DIABETES_MANIFEST = ModuleManifest(
    name="diabetes",
    version="1.0.0",
    condition="E11",
    url_prefix="/diabetes",  # Reserved module namespace, NOT an exposed HTTP prefix.
    tags=["diabetes"],
    supported_languages=["fr", "ar-MA", "ar"],
    # Only the canonical, reachable chat endpoint receives vital triage.
    # /diabetes stays a RESERVED prefix; P3 HTTP aliases are dormant (#929).
    interactive_endpoints=["/api/v1/ai/chat"],
    acquisition_event="log_created",
)
