# IAMINA single cross-platform launcher audit — 2026-08-19

## Goal
Keep one canonical host launcher that runs the same orchestration on Windows and macOS.

## Audit result
Previous launcher surface was duplicated across `dev.ps1`, `dev.sh`, `IAMINA.bat` and `IAMINA.command`. Those paths diverged in setup behavior, Flutter handling and operating-system semantics.

The replacement is `IAMINA.py`, implemented only with Python standard-library orchestration plus the project's existing Python/Flutter/Docker dependencies.

## Contract
- Python 3.12 required on both platforms.
- Flutter 3.41.7 required and validated on both platforms.
- backend: `127.0.0.1:8008`.
- frontend: `localhost:8009`.
- `.env` created from `.env.example` when absent.
- virtual environment and backend packages synchronized.
- migrations applied and demo setup attempted.
- Redis started best-effort when Docker exists; Redis network failures are time-bounded when unavailable.
- backend launcher readiness means the Django server is accepting local TCP connections on `8008`; it is deliberately independent from dependency-sensitive application health checks.
- frontend readiness uses direct localhost HTTP with ambient proxy settings bypassed.
- Windows child process trees are terminated as a unit; Unix children use process groups.

## Removed duplicated launchers
- `dev.ps1`
- `dev.sh`
- `IAMINA.bat`
- `IAMINA.command`

## Cross-platform proof gate
`.github/workflows/developer-portability.yml` runs the same `IAMINA.py` on both `windows-latest` and `macos-latest` with:

```text
python -m py_compile IAMINA.py
python IAMINA.py --check
python IAMINA.py --smoke --no-browser --no-redis
python IAMINA.py --check
```

The smoke intentionally performs the real bootstrap path: venv creation, backend dependency installation, migrations, demo setup attempt, Flutter validation/dependency sync, backend TCP readiness on `8008`, frontend HTTP readiness on `8009`, and cleanup verification.

The lot is not certified until both real launcher smoke jobs and the required regression workflows pass on the exact PR head.

## Double-click boundary
A single repository file cannot be guaranteed as a native double-click executable on both Windows and macOS because the operating systems use different executable/file-association models. The guaranteed portable invocation is Python 3.12 (`python IAMINA.py` on Windows, `python3 IAMINA.py` on macOS). Native desktop launch artifacts, if required later, must be generated from this single source rather than duplicating launcher logic.
