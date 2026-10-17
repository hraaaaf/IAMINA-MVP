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
# API_BASE_URL is the backend origin only: Flutter services append /api/v1.
IAMINA_REVIEW_VERCEL_PROJECT_ID="prj_AYaUi32KTDHak8I7dmdQpDrqd8SI"
IAMINA_CERTIFIED_API_BASE_URL="https://iamina-certified.vercel.app"

# Fail closed on Vercel if this Flutter build is ever invoked by another
# project. This prevents the certified backend project from accidentally
# publishing the Flutter SPA when its Root Directory is misconfigured.
if [ -n "${VERCEL_PROJECT_ID:-}" ] && [ "$VERCEL_PROJECT_ID" != "$IAMINA_REVIEW_VERCEL_PROJECT_ID" ]; then
  echo "ERROR: refusing Flutter build for Vercel project $VERCEL_PROJECT_ID; expected $IAMINA_REVIEW_VERCEL_PROJECT_ID" >&2
  exit 64
fi

# The review project has one canonical backend origin. Always override any
# stale project-level API_BASE_URL when Vercel exposes the expected project ID.
if [ "${VERCEL_PROJECT_ID:-}" = "$IAMINA_REVIEW_VERCEL_PROJECT_ID" ]; then
  case "${VERCEL_ENV:-}" in
    preview)
      # A synthetic Web Preview MUST use the uniquely deployed synthetic API,
      # never the stable backend alias (which can address a different database).
      # The fixed project/account suffix prevents another Vercel app or origin
      # from being injected into the web bundle.
      if [[ ! "${IAMINA_REVIEW_PREVIEW_API_BASE_URL:-}" =~ ^https://iamina-certified-[a-z0-9-]+-achraf-benmoussa-s-projects\\.vercel\\.app/?$ ]]; then
        echo "ERROR: Preview requires the exact IAMINA synthetic backend deployment URL" >&2
        exit 64
      fi
      API_BASE_URL="${IAMINA_REVIEW_PREVIEW_API_BASE_URL%/}"
      IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false
      ;;
    production)
      # Existing production routing remains unchanged.
      API_BASE_URL="$IAMINA_CERTIFIED_API_BASE_URL"
      IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true
      ;;
    *)
      echo "ERROR: refusing IAMINA Web build for unknown Vercel environment" >&2
      exit 64
      ;;
  esac
fi

# Defensive normalization: some Vercel builds can inherit a legacy project-
# level API_BASE_URL ending in /api/v1. Flutter services append their own
# /api/v1 paths, so strip that suffix even when VERCEL_PROJECT_ID is absent.
if [ -n "${API_BASE_URL:-}" ]; then
  API_BASE_URL="${API_BASE_URL%/}"
  API_BASE_URL="${API_BASE_URL%/api/v1}"
fi

if [ -n "${API_BASE_URL:-}" ]; then
  echo "Building IAMINA web with configured backend: $API_BASE_URL"
  flutter build web --release \
    --dart-define=API_BASE_URL="$API_BASE_URL" \
    --dart-define=IAMINA_REMOTE_ACCOUNT_ENROLLMENT="${IAMINA_REMOTE_ACCOUNT_ENROLLMENT:-false}"
else
  echo "Building IAMINA frontend-only demo: no API_BASE_URL configured"
  flutter build web --release --dart-define=IAMINA_OFFLINE_DEMO=true
fi
