# IAMINA local launcher

`IAMINA.py` is the single source of launcher logic and remains the canonical CLI entry point.

Guaranteed CLI paths:

- Windows: `python IAMINA.py`
- macOS: `python3 IAMINA.py`

Native double-click entry points are deliberately thin wrappers over that same file:

- Windows: double-click `IAMINA.bat`
- macOS: double-click `IAMINA.command`

The wrappers do not duplicate bootstrap, dependency, port, readiness or process-management logic. They only move to the repository root, invoke `IAMINA.py`, forward arguments and preserve its exit code. `IAMINA.command` is versioned executable so Finder can open it through Terminal after a normal Git checkout.

## Developer bootstrap contract

Application dependencies are installed/synchronized by `IAMINA.py`:

- creates/reuses the Python `venv`
- installs `backend/requirements.txt`
- creates `.env` from `.env.example` when missing
- applies Django migrations and attempts demo setup
- runs `flutter pub get`

Host toolchains are not silently installed because Python, Flutter, Docker Desktop and Git may require OS package managers, administrator approval or interactive installers. Instead the launcher now diagnoses them and prints platform-specific remediation commands.

Pinned Python and Flutter versions are read from `.tool-versions`; the launcher no longer maintains duplicate version constants.

Use:

```bash
python IAMINA.py --doctor
```

The doctor reports PASS/WARN/FAIL for the supported host platform, Python, Git, Flutter, Docker engine state and ports 8008/8009. Docker remains optional for the convenience host path, but missing or stopped Docker is reported explicitly.

## Local demo behavior

The canonical host launcher starts Flutter with `--dart-define=IAMINA_OFFLINE_DEMO=true`.

This enables the existing local demo authentication path without Firebase. The login screen's demo action can therefore enter the local audit/demo session when Firebase migration is disabled, instead of failing through `signInAnonymously()`.

This define is a local developer-launcher behavior only. It does not enable offline demo mode in deployment or production builds.

## Redis behavior

When Docker is available, the launcher starts the local `redis:7-alpine` container and now requires a real `redis-cli ping` → `PONG` readiness proof before reporting Redis as ready.

The launcher distinguishes:

- Docker not installed
- Docker CLI installed but engine not running
- Redis already running and healthy
- Redis container started but failed readiness

If Redis is unavailable, the host launcher preserves the existing bounded backend fallback. Docker/PostgreSQL/Redis integration remains the canonical validation path before merge.

Runtime endpoints:

- backend: `http://127.0.0.1:8008`
- frontend: `http://localhost:8009`

The portability workflow certifies the real path on both operating systems: native wrapper → `IAMINA.py` → full bootstrap → backend/frontend reachability → cleanup.

See `docs/DEPENDENCIES.md` for prerequisites and `docs/assessments/2026-08-19-single-cross-platform-launcher-audit.md` for the underlying launcher audit and certification contract.
