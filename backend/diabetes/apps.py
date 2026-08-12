from django.apps import AppConfig


class DiabetesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "diabetes"
    verbose_name = "Diabetes (Disease Capsule)"

    def ready(self) -> None:
        from core.safety_registry import TRIAGE_REGISTRY
        # Register the chat endpoint as a triage-eligible path.
        # Both paths must remain registered: old Flutter path + new P3 namespaced path.
        TRIAGE_REGISTRY.register_path("/api/v1/ai/chat")
        TRIAGE_REGISTRY.register_path("/api/v1/diabetes/ai/chat")  # P3: new namespaced path

        # RGPD Art. 17: invalidate patient session cache on account deletion.
        from core.account_hooks import register_account_delete_hook
        from diabetes.services.session_cache import invalidate as _invalidate_session
        register_account_delete_hook(lambda pid, uid: _invalidate_session(pid))

        # RGPD audit sink — lets core/account record audit events without
        # importing diabetes.models.AuditLog (import-linter boundary).
        from core.audit import register_audit_sink
        from diabetes.models import AuditLog
        register_audit_sink(
            lambda patient, action, request=None, **meta: AuditLog.record(
                patient, action, request, **meta
            )
        )

        # P1-EVIDENCE: register the evidence-gated diabetes authority boundary.
        from core.registry import ModuleRegistry
        from diabetes.api.v1.logs import router as _logs_router
        from diabetes.manifest import DIABETES_MANIFEST
        from diabetes.services.clinical.evidence_engine import EvidenceGuardedDiabetesEngine
        ModuleRegistry.register(DIABETES_MANIFEST, EvidenceGuardedDiabetesEngine, _logs_router)

        # Companion persistence ports (memory + conversation). Clinical data flows
        # through the registered diabetes engine contract, not through ports.
        from core.companion.ports import (
            register_conversation_store,
            register_snapshot_store,
        )
        from diabetes.companion_adapters import (
            DiabetesConversationStore,
            DiabetesSnapshotStore,
        )
        register_snapshot_store(DiabetesSnapshotStore())
        register_conversation_store(DiabetesConversationStore())
