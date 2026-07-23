#!/bin/bash
# IAmina local dev — setup (if needed) + backend + frontend in one shot.
# Usage: ./dev.sh
# Ctrl-C stops both services cleanly.
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ── One-time setup (idempotent) ───────────────────────────────────────────────

if [ ! -d venv ]; then
  echo "==> First run: setting up environment"
  echo "--> Creating Python venv"
  python3 -m venv venv
fi

source venv/bin/activate

# Sync Python deps silently (fast no-op when already installed)
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "--> .env created from .env.example — fill in API keys before using AI features"
fi

cd backend
python manage.py migrate --run-syncdb -v 0 2>/dev/null
python manage.py setup_demo 2>/dev/null || true
cd "$ROOT"

if ! command -v flutter &>/dev/null; then
  echo ""
  echo "  ERROR: flutter not found. Install Flutter 3.41.7 or run: mise install"
  echo "  https://docs.flutter.dev/get-started/install"
  echo ""
  exit 1
fi

cd frontend && flutter pub get 2>/dev/null; cd "$ROOT"

# ── Launch services ───────────────────────────────────────────────────────────

cleanup() {
  echo ""
  echo "==> Shutting down..."
  kill "$BACKEND_PID" 2>/dev/null
  exit 0
}
trap cleanup INT TERM

echo ""
echo "==> Starting IAmina"
echo "    Backend  → http://127.0.0.1:8001"
echo "    Frontend → http://localhost:3000"
echo "    Demo     → dev@iamina.app"
echo ""

# Backend in background
source venv/bin/activate
cd backend && python manage.py runserver 8001 &
BACKEND_PID=$!
cd "$ROOT"

# Flutter in foreground (Ctrl-C here stops both)
cd frontend && flutter run -d web-server \
  --web-port 3000 \
  --web-hostname localhost \
  --dart-define=DEMO_EMAIL=dev@iamina.app \
  --dart-define=DEMO_PASSWORD=IAmina2026! \
  --dart-define=API_BASE_URL=http://127.0.0.1:8001
