# Pilot API compatibility contract

Status: engineering contract for P5-4. This document does **not** certify a signed mobile release or a real-device upgrade.

## Goal

Keep an explicit old-client/new-backend compatibility window so a pilot build can distinguish:

- `update_required`: client is below the minimum supported version/build;
- `update_available`: client remains supported but a newer pilot build exists;
- `current`: client matches the latest configured pilot build;
- `client_ahead`: development/future client is newer than the configured latest build; compatibility is intentionally unknown until the backend contract catches up;
- `version_unknown`: client did not provide complete version metadata, so the server does not falsely claim compatibility.

## Public contract

`GET /api/v1/app-compatibility`

Optional query parameters:

- `client_version`: stable SemVer `MAJOR.MINOR.PATCH`;
- `client_build`: positive monotonically increasing integer.

A deterministic compatibility decision requires both fields. Missing metadata remains non-blocking for legacy/dev clients but is reported as `version_unknown` with `compatible: null`.

The response exposes:

- `api_contract_version`;
- minimum supported app version/build;
- latest configured app version/build;
- echoed client version/build;
- `status`;
- `compatible`;
- `update_required`;
- `update_available`.

Malformed supplied client metadata returns HTTP 422. Invalid server policy fails closed with HTTP 503.

The generated exact-head contract is retained in `docs/api/openapi.json`; CI rejects the PR if this schema becomes stale.

## Release configuration

Before producing a signed pilot build, operators must set these backend environment values to match the signed artifact ledger:

- `PILOT_MIN_SUPPORTED_APP_VERSION`;
- `PILOT_MIN_SUPPORTED_BUILD`;
- `PILOT_LATEST_APP_VERSION`;
- `PILOT_LATEST_BUILD`.

Defaults are currently `0.1.0+1`, matching `frontend/pubspec.yaml`. The minimum must never exceed the latest configured version/build.

## Compatibility window policy

1. Keep at least the immediately previous supported pilot build compatible while N is being rolled out, unless a safety/security issue requires a forced update.
2. Raise the minimum only after the N-1 → N upgrade path and local Drift preservation have been proven on real devices.
3. A forced update is a release/governance decision, not an incidental backend deploy side effect.
4. API changes inside the active window must remain backward compatible or be introduced behind a new contract version/path.
5. A `client_ahead` response never asserts compatibility. It reports `compatible: null` because an older backend cannot safely certify a newer client contract.
6. Rollback is forward-fix oriented. Do not instruct users to clear app storage as routine recovery.

## Remaining P5-4 evidence

This repository contract closes only the API-window engineering gap. P5-4 still requires external/human evidence for signed Android/iOS artifacts, Firebase identity decision, real-device install/update, N-1 → N data preservation, recovery rehearsal, artifact hashes, and no-repo/no-dev-tool installation instructions.
