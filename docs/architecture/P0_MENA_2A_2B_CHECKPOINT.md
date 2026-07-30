# P0-MENA-2A/2B checkpoint

## Canonical persistence

`PatientLocalePreference` is the authoritative cross-cutting locale record linked one-to-one to `BasePatientProfile`. Country, UI language, response language, script, transliteration, dialect, glucose units and IANA timezone are independent dimensions with independent provenance.

Only `user_confirmed` values may control runtime behavior. Suggested and defaulted values remain non-authoritative.

## Authenticated confirmation API

- `GET /api/v1/profile/locale` returns stored provenance and resolved runtime values.
- `PATCH /api/v1/profile/locale` confirms only explicitly supplied dimensions for `request.user`.
- `DELETE /api/v1/profile/locale/{dimension}` revokes one dimension without mutating the others.
- No patient identifier is accepted from the client.
- Explicit null updates are rejected; revocation uses the dedicated DELETE path.
- Invalid country, language, script, transliteration, dialect, glucose-unit and timezone values fail closed.

## Safety behavior

Location-derived suggestions cannot alter response language, emergency-country selection, units, timezone or rendering until the authenticated patient confirms the exact dimension. Revocation immediately restores the deterministic resolver fallback.
