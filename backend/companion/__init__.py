"""
IAmina brain — companion runtime package.

Dependency rule (P6.5): companion/ is condition-agnostic and MUST NOT import
any module package (diabetes, hypertension, ...). All module-specific data —
memory persistence, conversation history, clinical context, narrative inputs,
offline alerts — is resolved through the chassis ports in core.companion.ports,
which the active module fills with adapters at startup (DiabetesConfig.ready()).

- Imports from llm.* (factory, pseudonymizer, base, etc.) — allowed (chassis).
- Imports from core.companion.ports — allowed (chassis).
- Imports from diabetes.* — FORBIDDEN. Guarded by core/tests/test_companion_ports.py.

See docs/architecture/platform_p6.5_companion_seam_PLAN.md.
"""
