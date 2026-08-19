# IAMINA — Developer dependencies

Status: **CANONICAL DEVELOPER REFERENCE**

This document describes the tools required to develop and launch IAMINA locally. Package manifests remain the source of truth for application libraries; do not duplicate or manually pin their full contents here.

## Sources of truth

- Runtime/toolchain versions: `.tool-versions`
- Backend Python packages: `backend/requirements.txt`
- Frontend/Dart packages: `frontend/pubspec.yaml` and `frontend/pubspec.lock`
- Container services/images: `docker-compose.yml` and `docker-compose.override.yml`
- Environment variables: `.env.example`
- Cross-platform local launcher: `IAMINA.py`

## Required on every developer machine

| Dependency | Required version / role | Windows | macOS |
| --- | --- | --- | --- |
| Git | Current supported release | Required | Required |
| Python | 3.12 | Required | Required |
| Flutter | 3.41.7 | Required for frontend | Required for frontend |
| Browser | Chromium/Chrome-class browser for Flutter web | Required | Required |

Python and Flutter versions are pinned in `.tool-versions`.

## Reproducibility boundary

The Flutter application has `pubspec.lock`, so its resolved package graph can be reproduced from the lockfile.

The backend currently uses version ranges in `backend/requirements.txt` rather than a fully frozen lockfile. A fresh install therefore resolves package versions allowed by those ranges at install time. CI remains the authority for accepted resolutions. Do not infer that every backend package is exactly pinned merely because the toolchain version is pinned.

The README may describe the currently targeted backend stack at a higher level while `backend/requirements.txt` is the installation contract. Any future decision to freeze the full Python dependency graph should be handled as a dedicated dependency-management change with CI proof.

## Canonical local launcher

There is one versioned host launcher for Windows and macOS:

```text
IAMINA.py
```

Run it with the pinned Python 3.12 interpreter:

```bash
# Windows
python IAMINA.py

# macOS
python3 IAMINA.py
```

It performs the same orchestration on both platforms:

- creates/reuses `venv`
- installs backend requirements
- creates `.env` from `.env.example` when missing
- applies Django migrations and attempts demo setup
- validates Flutter 3.41.7
- runs `flutter pub get`
- starts Redis through Docker when Docker is available, otherwise degrades gracefully with bounded cache connection/read timeouts
- starts backend on `http://127.0.0.1:8008`
- starts frontend on `http://localhost:8009`
- probes localhost directly without ambient HTTP(S) proxies
- waits for both services to respond before opening the browser
- stops child process trees on exit

No `.bat`, `.ps1`, `.sh` or `.command` launcher is canonical anymore.

### Double-click boundary

A single file type cannot be guaranteed to be natively double-click executable on both Windows and macOS because the operating systems use different launcher/file-association models. `IAMINA.py` is the single cross-platform source of truth. Double-click works only where `.py` files are associated with Python; terminal invocation above is the guaranteed path.

If a future product requirement demands guaranteed desktop double-click without a terminal, package native per-OS launch artifacts from this same source rather than reintroducing duplicated launcher logic into the repository.

## Recommended canonical backend environment

Docker Desktop remains the canonical backend integration path for reproducible PostgreSQL + Redis development:

```bash
cp .env.example .env
docker compose up --build
```

The host launcher is a convenience development path. It does not replace PostgreSQL-backed Docker validation before merge.

## Backend Python dependencies

Install from the manifest only:

```bash
python -m pip install -r backend/requirements.txt
```

Notable groups currently include Django/django-ninja, PostgreSQL support, Firebase migration compatibility, Redis integration, cryptography, tests, document parsing and OCR bindings.

`pytesseract` is a Python binding. Any runtime path that actually invokes Tesseract OCR also requires the native Tesseract executable to be installed and discoverable. This is optional unless that OCR path is being exercised.

## Frontend dependencies

Install from Flutter manifests only:

```bash
cd frontend
flutter pub get
```

The frontend currently includes routing, Firebase migration compatibility, secure storage, Drift/SQLite, networking, voice capture/TTS, mobile OCR, file import, charts, serialization and test/code-generation tooling.

Some plugins are platform-specific. In particular, ML Kit OCR is intended for mobile iOS/Android rather than Flutter web/desktop.

## iOS-only development

Xcode is required only for iOS simulator/device/build work. It is not required for backend development or Flutter web analyze/tests.

## Launcher certification commands

The launcher exposes deterministic validation modes used by CI:

```bash
python IAMINA.py --check
python IAMINA.py --smoke --no-browser --no-redis
python IAMINA.py --check
```

The smoke deliberately exercises the full bootstrap path and must prove that backend `8008` and frontend `8009` are both reachable, then cleanly stop them and release both ports.

## Validation after dependency changes

When changing a dependency or toolchain version, update the authoritative manifest first, then run the relevant checks:

```bash
# Backend
python backend/manage.py check
python -m pytest backend --tb=short -q

# Frontend
cd frontend
flutter pub get
flutter analyze --no-fatal-infos
flutter test --no-pub
```

Dependency documentation must be updated in the same PR if prerequisites or developer launch behavior changes.
