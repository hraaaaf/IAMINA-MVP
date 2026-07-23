"""
ModuleManifest — frozen dataclass every condition module declares at startup.

The chassis reads this to:
- Mount the module's Django Ninja router at the declared url_prefix
- Register interactive_endpoints into AppendOnlyTriageRegistry
- Configure retention dashboard cohort queries via acquisition_event
- Tag OpenAPI docs

See docs/architecture/module-contract-spec.md section 1 for full spec.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModuleManifest:
    name: str
    # Human-readable module name. Example: "Diabetes Companion"

    version: str
    # Semver string. Example: "1.0.0"

    condition: str
    # Snake-case condition slug. Example: "diabetes", "hypertension"

    url_prefix: str
    # Static string — NO path params. Django Ninja add_router() does not accept
    # path parameters in prefixes (expert review C6, ADR-0008).
    # Example: "/v1/diabetes"  NOT "/v1/{condition}/"

    tags: list[str]
    # OpenAPI tags for this module's endpoints.
    # Example: ["diabetes", "glucose"]

    supported_languages: list[str]
    # BCP-47 language codes this module supports.
    # Example: ["fr", "ar-MA", "en"]

    interactive_endpoints: list[str]
    # Endpoint paths that require TriageVitalMiddleware protection.
    # Registered into AppendOnlyTriageRegistry at startup via AppConfig.ready().
    # Example: ["/api/v1/ai/chat"]

    acquisition_event: str
    # ObservabilityEvent type that marks a new user acquisition for this module.
    # Used by the retention dashboard cohort query (D1/D7/D30/D90).
    # Example: "LOG_CREATED"
