"""
External integrations — anti-corruption layer (future home for Phase MVP+1).

Empty package today. Per AMINA_MVP_PLAN.md §6 (Enterprise Architect) we
anticipate three categories of sub-packages:

- `cgm/` — Libre LibreLinkUp, Dexcom Share/G7, Medtronic CareLink.
- `ehr/` — FHIR R4, Doctolib, Maiia, DMP.
- `identity/` — OIDC providers (Google), France Connect, Morocco.

Each sub-package will expose a common interface (rate limit, backoff,
health check) and an adapter per vendor. This package sits at the
backend root (not inside `tracking/` or `core/`) because integrations
cross multiple aggregates — a CGM feed produces LogEntry rows *and*
updates PatientProfile flags.
"""
