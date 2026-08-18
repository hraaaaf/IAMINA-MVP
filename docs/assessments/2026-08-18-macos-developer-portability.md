# IAMINA — macOS developer portability certification

Status: **IMPLEMENTED / CERTIFICATION PENDING**

## Goal

Prove that a collaborator using macOS can clone IAMINA, bootstrap the supported development environment, run backend/frontend checks and prepare a PR without Windows-specific assumptions.

## Success criteria

1. fresh-clone bootstrap instructions explicitly create `.env` from `.env.example`;
2. Docker backend healthcheck uses a runtime primitive guaranteed by the image rather than an undeclared `curl` dependency;
3. macOS GitHub runner reports its host architecture;
4. tracked paths have no case-insensitive collisions;
5. `dev.sh` passes `bash -n` on macOS;
6. Python 3.12 installs backend dependencies and passes Django check + backend pytest on macOS host;
7. Flutter 3.41.7 passes pub get, analyze and tests on macOS host;
8. Apple Silicon Docker Desktop compatibility is claimed only if an arm64 Docker execution is actually observed.

## Baseline findings

- `.tool-versions`: Python 3.12 + Flutter 3.41.7.
- `.gitattributes`: LF normalization for shell/Python/YAML.
- canonical backend path: Docker Compose with PostgreSQL + Redis.
- canonical frontend path: host Flutter.
- defect found: Compose healthcheck depended on `curl`, absent from the backend runtime image.
- onboarding gap found: Compose requires `.env`, but the prior README quick-start did not explicitly create it.
- no prior `macos-latest` workflow certified host portability.

## Implementation

- Compose healthcheck now executes Python `urllib.request`, which is guaranteed by the Python runtime already present in the backend image.
- `docs/DEVELOPER_MACOS.md` defines the fresh-clone, Docker backend, Flutter host, host-backend smoke and PR paths.
- `.github/workflows/macos-developer-portability.yml` performs native macOS portability certification and reports the actual runner architecture.

## Explicit boundary

This lot does not alter patient runtime, clinical logic, AI provider behavior, database schema or UI. It does not deploy production Vercel.

Preview Vercel side effects for this PR were explicitly authorized by the owner for this lot only.

macOS host certification does not automatically equal Apple Silicon Docker Desktop certification. If the GitHub runner reports a non-arm64 architecture, an actual arm64 Docker run remains the external manual proof gate.

## Closeout gate

Exact-head standard CI + migration drift + macOS portability workflow must pass. Branch freshness against `main` must then be verified before expected-head merge. Post-merge checks and canonical documentation synchronization are required before declaring this lot closed.
