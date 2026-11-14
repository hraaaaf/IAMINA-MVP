#!/usr/bin/env bash
# D2 synthetic-only, no-clinical-DB Preview build.
set -euo pipefail
D2_BRANCH="feat/d2-guest-bootstrap-no-db-20261114"
FRONTEND_PROJECT="prj_AYaUi32KTDHak8I7dmdQpDrqd8SI"
if [[ "${VERCEL_ENV:-}" != "preview" ||
      "${VERCEL_PROJECT_ID:-}" != "$FRONTEND_PROJECT" ||
      "${VERCEL_GIT_COMMIT_REF:-}" != "$D2_BRANCH" ]]; then
  echo "DENY: wrong D2 Preview environment, project or branch" >&2
  exit 64
fi
for forbidden in DATABASE_URL POSTGRES_URL SECRET_KEY API_BASE_URL \
  FIREBASE_CREDENTIALS_PATH FIREBASE_SERVICE_ACCOUNT \
  GOOGLE_APPLICATION_CREDENTIALS VERCEL_AUTOMATION_BYPASS_SECRET; do
  if [[ -n "$(printenv "$forbidden" || true)" ]]; then
    echo "DENY: forbidden D2 Preview variable: $forbidden" >&2
    exit 64
  fi
done
if [[ ! "${IAMINA_REVIEW_PREVIEW_API_BASE_URL:-}" =~ ^https://iamina-certified-[a-z0-9-]+-achraf-benmoussa-s-projects\.vercel\.app/?$ ]]; then
  echo "DENY: missing immutable synthetic D2 API" >&2
  exit 64
fi
FLUTTER_VERSION="3.41.0"
FLUTTER_DIR="/tmp/flutter-$FLUTTER_VERSION"
if [[ ! -x "$FLUTTER_DIR/bin/flutter" ]]; then
  git clone --depth 1 --branch "$FLUTTER_VERSION" https://github.com/flutter/flutter.git "$FLUTTER_DIR"
fi
export PATH="$FLUTTER_DIR/bin:$PATH"
flutter config --enable-web
flutter pub get
# All browser auth requests are same-origin and go through an identity-only BFF.
# The runtime D2 flag short-circuits clinical DB/AI/profile initialization.
flutter build web --release --no-web-resources-cdn \
  --dart-define=API_BASE_URL=https://d2-no-clinical-backend.invalid \
  --dart-define=ENABLE_FIREBASE_MIGRATION=false \
  --dart-define=IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true \
  --dart-define=IAMINA_REMOTE_ACCOUNT_SIGN_IN=true \
  --dart-define=IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED=true \
  --dart-define=IAMINA_OFFLINE_DEMO=false \
  --dart-define=IAMINA_AUDIT_ACCESS=false \
  --dart-define=IAMINA_D1_PREVIEW_AUTH_CHOICES=true \
  --dart-define=IAMINA_D2_GUEST_NO_DB=true
echo "D2_PREVIEW_DB_FREE_VISITOR_BUILD=PASS"
