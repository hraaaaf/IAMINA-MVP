# IAMINA — macOS developer bootstrap

Status: **SUPPORTED / HOST ARM64 CI CERTIFIED**

## Goal

A collaborator on macOS can clone IAMINA, bootstrap the canonical backend/frontend development environment, run the required local checks, and open a focused PR without relying on Windows-only tooling.

## Verified certification

The macOS portability workflow has passed on a GitHub-hosted Apple Silicon runner reporting `macos-26-arm64` / `uname -m = arm64`, including backend tests, Flutter analyze/tests and case-collision checks.

This certifies the host macOS development path. It does not by itself certify Docker Desktop running locally on Apple Silicon hardware.

## Prerequisites

- Git
- Docker Desktop for the canonical containerized backend path
- Python 3.12
- Flutter 3.41.7
- Xcode only when iOS build/simulator work is required

The repository pins Python and Flutter in `.tool-versions`. See `docs/DEPENDENCIES.md` for the canonical developer dependency reference.

## Fresh clone

```bash
git clone <repo>
cd IAMINA-MVP
cp .env.example .env
```

The `.env` copy is required because `docker-compose.yml` declares it through `env_file`. Development defaults may be used without provider credentials; never commit local secrets.

## Cross-platform host launch

The repository has one host launcher shared with Windows:

```bash
python3 IAMINA.py
```

It starts:

- backend: `http://127.0.0.1:8008`
- frontend: `http://localhost:8009`

It validates the pinned Flutter version, waits for both services to respond before opening the browser and cleans up child process trees when stopped.

A single file type cannot guarantee native Finder double-click execution on both macOS and Windows. `IAMINA.py` is therefore the single portable source of truth; terminal execution is the guaranteed cross-platform path.

## Canonical backend path

```bash
docker compose up --build
```

Then, in another terminal:

```bash
docker compose run --rm backend python manage.py setup_demo
```

The development override publishes the API on `http://127.0.0.1:8001/api/v1/`.

## Canonical frontend path

```bash
cd frontend
flutter pub get
flutter analyze --no-fatal-infos
flutter test --no-pub
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8001
```

## Host backend smoke path

The Docker backend remains canonical, but macOS CI also verifies that the Python host environment is not accidentally Windows-specific:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/manage.py check
python -m pytest backend --tb=short -q
```

## Launcher portability

The same `IAMINA.py` file is certified through the real bootstrap path on macOS and Windows. Its CI contract is:

```bash
python IAMINA.py --check
python IAMINA.py --smoke --no-browser --no-redis
python IAMINA.py --check
```

The smoke must prove both port `8008` backend health and frontend readiness on `8009`, followed by cleanup that releases both ports.

## Git workflow

```bash
git checkout main
git pull origin main
git checkout -b feature/short-description
# work + local checks
git push -u origin feature/short-description
```

Open a focused PR to `main`. GitHub CI remains the merge authority even when local Mac checks pass.

## Apple Silicon boundary

The host ARM64 path is certified by the native macOS workflow. Docker Desktop arm64 compatibility remains a separate manual proof gate until Docker itself is executed and observed on an Apple Silicon developer machine.

The canonical container images are official multi-platform candidates (`python:3.12-slim`, `postgres:16-alpine`, `redis:7-alpine`), but IAMINA does not claim Apple Silicon Docker certification without that execution proof.

## iOS boundary

The repository contains the Flutter iOS project. The macOS portability certification covers collaborator development for backend + Flutter analysis/tests/web execution. It does **not** claim signing, simulator/device, CocoaPods, App Store, or production iOS release certification unless those checks are added and pass separately.
