#!/usr/bin/env bash
set -euo pipefail

FLUTTER_VERSION="3.41.0"
FLUTTER_DIR="/tmp/flutter-$FLUTTER_VERSION"

if [ ! -x "$FLUTTER_DIR/bin/flutter" ]; then
  git clone --depth 1 --branch "$FLUTTER_VERSION" https://github.com/flutter/flutter.git "$FLUTTER_DIR"
fi

export PATH="$FLUTTER_DIR/bin:$PATH"
flutter config --enable-web
flutter pub get

# The public review frontend is a separate Vercel project from the certified
# Django backend. Bind only that frontend project to the live backend so the
# backend project itself and local/demo builds keep their existing behavior.
IAMINA_REVIEW_VERCEL_PROJECT_ID="prj_AYaUi32KTDHak8I7dmdQpDrqd8SI"
IAMINA_CERTIFIED_API_BASE_URL="https://iamina-certified.vercel.app/api/v1"

if [ -z "${API_BASE_URL:-}" ] && [ "${VERCEL_PROJECT_ID:-}" = "$IAMINA_REVIEW_VERCEL_PROJECT_ID" ]; then
  API_BASE_URL="$IAMINA_CERTIFIED_API_BASE_URL"
fi

if [ -n "${API_BASE_URL:-}" ]; then
  echo "Building IAMINA web with configured backend: $API_BASE_URL"
  flutter build web --release --dart-define=API_BASE_URL="$API_BASE_URL"
else
  echo "Building IAMINA frontend-only demo: no API_BASE_URL configured"
  flutter build web --release --dart-define=IAMINA_OFFLINE_DEMO=true
fi
