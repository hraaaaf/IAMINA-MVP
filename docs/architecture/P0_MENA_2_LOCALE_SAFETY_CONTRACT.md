# P0-MENA-2 — Locale + Safety Contract

Status: **ACTIVE DESIGN CONTRACT**  
Started: 2026-07-30  
Branch: `feat/p0-mena-locale-safety-contract`

## Goal

Represent locale, language and safety settings as explicit independent patient choices. Location may suggest values, but it must never silently determine language, emergency resources, units, consent or clinical behaviour.

## Canonical dimensions

The application must model these dimensions separately:

1. `country_code`
   - ISO 3166-1 alpha-2 uppercase code.
   - Used only for country-scoped configuration explicitly documented for that country.

2. `ui_language`
   - Language used by the application interface.
   - Baseline enabled values: `fr`, `ar`, `en`.

3. `response_language`
   - Language requested for companion responses.
   - Independent from the UI language.

4. `script_preference`
   - Writing-system preference, separate from language and dialect.
   - Initial values: `latin`, `arabic`.

5. `transliteration_preference`
   - Explicit preference for transliterated output.
   - Initial values: `none`, `latin_arabic`.

6. `dialect`
   - Explicit optional dialect selection.
   - Initial enabled dialect: `ar-MA` only after its safety corpus and parity gates pass.
   - `null` means no dialect-specific behaviour.

7. `glucose_unit`
   - Explicit value: `mg/dL` or `mmol/L`.
   - Must not be inferred from language.

8. `timezone`
   - IANA timezone identifier, for example `Africa/Casablanca`.
   - Must not be represented as a fixed UTC offset.

## Provenance and confirmation

Every dimension must carry explicit provenance:

- `user_confirmed`: accepted or selected by the authenticated patient;
- `suggested`: proposed from device, account or location context but not yet accepted;
- `defaulted`: deterministic product fallback where no suggestion is available.

Only `user_confirmed` values may control:

- response language or dialect;
- glucose units;
- timezone-sensitive interpretation;
- country-specific emergency resources;
- RTL or transliteration behaviour that changes patient-facing meaning.

Suggested values are display-only until confirmation.

## Deterministic fallback

When a confirmed response setting is unavailable or unsupported:

1. use confirmed Modern Standard Arabic (`ar`) when Arabic script is confirmed;
2. otherwise use confirmed English (`en`) when available;
3. otherwise use French (`fr`).

A dialect must never silently fall back to another dialect. Unsupported dialect output falls back to its documented baseline language.

## Safety invariants

- Country does not determine language.
- Language does not determine country.
- UI language does not automatically determine response language.
- Dialect does not bypass the same clinical and safety rules as its baseline language.
- Transliteration is a rendering/input dimension, not a weaker safety mode.
- Emergency resources require an explicit confirmed country and a versioned source record.
- Missing or unconfirmed country-specific safety configuration fails closed to the documented generic safe path.
- Clinical thresholds, refusals and triage remain deterministic and locale-independent.
- External providers receive only the minimum confirmed locale fields required for the registered purpose.

## Tranche sequence

### P0-MENA-2A — Canonical preference model

- inventory existing language, country, unit and timezone fields;
- add one authoritative schema with independent dimensions and provenance;
- preserve existing patients through an explicit migration strategy;
- expose a server-side resolver that returns confirmed values plus deterministic fallbacks;
- prove location suggestions cannot mutate confirmed settings.

### P0-MENA-2B — Confirmation API and Flutter flow

- authenticated read/update API;
- no client-supplied patient ownership identifier;
- explicit confirmation and revocation of suggested values;
- deterministic validation and safe error UX.

### P0-MENA-2C — Fallback, RTL and rendering parity

- deterministic language fallback;
- complete RTL coverage for enabled Arabic flows;
- script and transliteration rendering tests.

### P0-MENA-2D — Country emergency-resource registry

- versioned resource registry with country, source URL/reference, owner and verification date;
- confirmed-country selection only;
- fail-closed generic path for absent or stale configuration.

### P0-MENA-2E — Native safety corpora and parity

- native-speaker-reviewed corpora for every enabled locale/dialect;
- Darija high-severity orthographic variants;
- parity tests for text, voice transcript, mixed-language and transliterated input.

## Merge gates

Every tranche remains draft until its affected scope passes:

- SQLite and PostgreSQL full suites;
- migration drift;
- Ruff and import-linter;
- API/OpenAPI drift;
- safety and anti-bypass tests;
- Flutter analyze and relevant widget/unit tests;
- secret hygiene.

## Non-goals

This lot does not:

- enable a new country automatically;
- approve a dialect before native safety review;
- replace deterministic clinical logic with model-based localisation;
- infer identity, nationality or medical context from device location;
- change the authentication-sovereignty roadmap.