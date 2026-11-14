#!/usr/bin/env bash
# Dedicated D1 Preview-only build of the ACTUAL Flutter main.dart.
# NO clinical DB, NO active API, NO patient enrollment.
set -euo pipefail

D1_PREVIEW_PROJECT_ID="prj_AYaUi32KTDHak8I7dmdQpDrqd8SI"
if [[ "$VERCEL_ENV" != "preview" || "$VERCEL_PROJECT_ID" != "$D1_PREVIEW_PROJECT_ID" ]]; then
  echo "DENY: not the protected isolated D1 Preview project" >&2
  exit 64
fi
if [[ "$VERCEL_GIT_COMMIT_REF" != "preview/d1-unified-synthetic-safehold-20261114" ]]; then
  echo "DENY: only the audited D1 test branch is supported" >&2
  exit 64
fi
for forbidden in DATABASE_URL POSTGRES_URL SECRET_KEY API_BASE_URL FIREBASE_CREDENTIALS_PATH FIREBASE_SERVICE_ACCOUNT GOOGLE_APPLICATION_CREDENTIALS VERCEL_AUTOMATION_BYPASS_SECRET; do
  if [[ -n "$(printenv "$forbidden" || true)" ]]; then
    echo "DENY: forbidden backend or clinical variable: $forbidden" >&2
    exit 64
  fi
done

FLUTTER_VERSION="3.41.0"
FLUTTER_DIR="/tmp/flutter-$FLUTTER_VERSION"
if [[ ! -x "$FLUTTER_DIR/bin/flutter" ]]; then
  git clone --depth 1 --branch "$FLUTTER_VERSION" https://github.com/flutter/flutter.git "$FLUTTER_DIR"
fi
export PATH="$FLUTTER_DIR/bin:$PATH"
flutter config --enable-web
flutter pub get

# Real application; fail-closed vault. Offline demo, Firebase and remote
# account enrollment disabled. Requests to .invalid cannot hit clinical API.
flutter build web --release --no-web-resources-cdn \
  --dart-define=API_BASE_URL=https://d1-no-clinical-backend.invalid \
  --dart-define=ENABLE_FIREBASE_MIGRATION=false \
  --dart-define=IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true \
  --dart-define=IAMINA_REMOTE_ACCOUNT_SIGN_IN=true \
  --dart-define=IAMINA_REMOTE_ACCOUNT_LOGIN_ENABLED=true \
  --dart-define=IAMINA_OFFLINE_DEMO=false \
  --dart-define=IAMINA_AUDIT_ACCESS=false \
  --dart-define=IAMINA_D1_PREVIEW_AUTH_CHOICES=true
echo "D1_PREVIEW_REAL_MAIN_SAFE_HOLD_BUILD=PASS"
