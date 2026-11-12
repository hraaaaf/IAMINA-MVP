#!/usr/bin/env bash
set -euo pipefail

# D1 PRF physical-iPhone test: dedicated branch preview, synthetic static files ONLY.
if [ "${VERCEL_GIT_COMMIT_REF:-}" = "research/d1-prf-iphone-preview-fixture-20261112" ]; then
  if [ "${VERCEL_ENV:-}" != "preview" ] || [ "${VERCEL_PROJECT_ID:-}" != "prj_AYaUi32KTDHak8I7dmdQpDrqd8SI" ]; then
    echo "D1 PRF: DENY non-preview or foreign Vercel project" >&2
    exit 64
  fi
  echo "D1 PRF: SYNTHETIC-ONLY STATIC PREVIEW (no Flutter or patient app)"
  mkdir -p build/web
  cp web/d1_webauthn_prf_gate_v1.js build/web/
  cp web/d1_webauthn_prf_harness.html build/web/index.html
  exit 0
fi

FLUTTER_VERSION="3.41.0"
FLUTTER_DIR="/tmp/flutter-$FLUTTER_VERSION"

if [ ! -x "$FLUTTER_DIR/bin/flutter" ]; then
  git clone --depth 1 --branch "$FLUTTER_VERSION" https://github.com/flutter/flutter.git "$FLUTTER_DIR"
fi

export PATH="$FLUTTER_DIR/bin:$PATH"
flutter config --enable-web
flutter pub get

# Fail-closed on incorrect/mismatched Drift worker and sqlite3 WASM.
bash scripts/verify_drift_web_assets.sh verify

# The public review frontend is a separate Vercel project from the certified
# Django backend. Bind only that frontend project to the live backend so the
# backend project itself and local/demo builds keep their existing behavior.
# API_BASE_URL is the backend origin only: Flutter services append /api/v1.
IAMINA_REVIEW_VERCEL_PROJECT_ID="prj_AYaUi32KTDHak8I7dmdQpDrqd8SI"
IAMINA_CERTIFIED_API_BASE_URL="https://iamina-certified.vercel.app"
IAMINA_W01_SESSION_PROBE=false
IAMINA_D2_PREVIEW_SAME_ORIGIN=false

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
      if [[ ! "${IAMINA_REVIEW_PREVIEW_API_BASE_URL:-}" =~ ^https://iamina-certified-[a-z0-9-]+-achraf-benmoussa-s-projects\.vercel\.app/?$ ]]; then
        echo "ERROR: Preview requires the exact IAMINA synthetic backend deployment URL" >&2
        exit 64
      fi
      # Pin the browser bundle to the stable W01 Web alias. All /api/v1
      # requests are now same-origin; the server-side OIDC bridge forwards
      # them to the immutable synthetic API deployment above.
      API_BASE_URL="https://iamina-review-git-preview-w0-f972e4-achraf-benmoussa-s-projects.vercel.app"
      # Only the D2 QA branch routes the patient account API to its own
      # immutable page origin. Existing W01 previews and production are unchanged.
      if [ "${VERCEL_GIT_COMMIT_REF:-}" = "fix/d2-main-integrated-20261109" ]; then
        IAMINA_D2_PREVIEW_SAME_ORIGIN=true
      fi
      # D7 hosted verification must use the *current immutable page origin*
      # for both login and account consent. Do not leak requests to the stale
      # W01 branch alias if some legacy consumer uses API_BASE_URL directly.
      if [ "${VERCEL_GIT_COMMIT_REF:-}" = "qa/d7-hosted-reconcile-20261110" ]; then
        IAMINA_D2_PREVIEW_SAME_ORIGIN=true
        API_BASE_URL="https://d7-qa-unrouted.invalid"
      fi
      IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false
      IAMINA_REMOTE_ACCOUNT_SIGN_IN=true
      if [ "${VERCEL_GIT_COMMIT_REF:-}" = "preview/w01-current-main-synthetic-20261104" ]; then
        IAMINA_W01_SESSION_PROBE=true
      fi
      ;;
    production)
      # Existing production routing remains unchanged.
      API_BASE_URL="$IAMINA_CERTIFIED_API_BASE_URL"
      IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true
      IAMINA_REMOTE_ACCOUNT_SIGN_IN=true
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
  if [ "$IAMINA_W01_SESSION_PROBE" = "true" ]; then
    echo "W01 ephemeral session-revocation diagnostic: PREVIEW ONLY"
    flutter test --no-pub --dart-define=IAMINA_W01_SESSION_PROBE=true \
      test/services/w01_revocation_probe_test.dart
  fi
  echo "Building IAMINA web with configured backend: $API_BASE_URL"
  flutter build web --release --no-web-resources-cdn \
    --dart-define=API_BASE_URL="$API_BASE_URL" \
    --dart-define=IAMINA_REMOTE_ACCOUNT_ENROLLMENT="${IAMINA_REMOTE_ACCOUNT_ENROLLMENT:-false}" \
    --dart-define=IAMINA_REMOTE_ACCOUNT_SIGN_IN="${IAMINA_REMOTE_ACCOUNT_SIGN_IN:-false}" \
    --dart-define=IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED="${IAMINA_D2_PREVIEW_SAME_ORIGIN}" \
    --dart-define=IAMINA_W01_SESSION_PROBE="${IAMINA_W01_SESSION_PROBE:-false}"
else
  echo "Building IAMINA frontend-only demo: no API_BASE_URL configured"
  flutter build web --release --no-web-resources-cdn --dart-define=IAMINA_OFFLINE_DEMO=true
fi
