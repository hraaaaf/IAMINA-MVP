# IAMINA — macOS developer bootstrap

Status: **SUPPORTED PATH / CI CERTIFICATION REQUIRED**

## Goal

A collaborator on macOS can clone IAMINA, bootstrap the canonical backend/frontend development environment, run the required local checks, and open a focused PR without relying on Windows-only tooling.

## Prerequisites

- Git
- Docker Desktop
- Python 3.12
- Flutter 3.41.7
- Xcode only when iOS build/simulator work is required

The repository pins Python and Flutter in `.tool-versions`.

## Fresh clone

```bash
git clone <repo>
cd IAMINA-MVP
cp .env.example .env
```

The `.env` copy is required because `docker-compose.yml` declares it through `env_file`. Development defaults may be used without provider credentials; never commit local secrets.

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

## Shell portability

`dev.sh` is a legacy helper, not the canonical startup path. It must nevertheless remain valid Bash syntax:

```bash
bash -n dev.sh
```

`.gitattributes` keeps shell, Python and YAML files on LF line endings.

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

GitHub-hosted macOS runners certify only the architecture reported by the runner itself. The workflow records `uname -m` as evidence. If the runner is not Apple Silicon, Docker Desktop arm64 compatibility remains a separate manual proof gate and must not be inferred from an Intel runner.

The canonical container images are official multi-platform candidates (`python:3.12-slim`, `postgres:16-alpine`, `redis:7-alpine`), but IAMINA does not claim Apple Silicon Docker certification until an arm64 Docker execution is observed.

## iOS boundary

The repository contains the Flutter iOS project. This macOS portability lot certifies collaborator development for backend + Flutter analysis/tests/web execution. It does **not** claim signing, simulator/device, CocoaPods, App Store, or production iOS release certification unless those checks are added and pass separately.
