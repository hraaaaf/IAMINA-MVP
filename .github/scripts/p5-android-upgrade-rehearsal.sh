#!/usr/bin/env bash
set -euo pipefail

: "${APP_ID:?APP_ID is required}"
mkdir -p rehearsal

wait_for_marker() {
  local marker="$1"
  local output="$2"
  local found=0
  for _ in $(seq 1 60); do
    adb logcat -d > "$output"
    if grep -Fq "$marker" "$output"; then
      found=1
      break
    fi
    sleep 2
  done
  test "$found" = "1"
}

echo "Emulator API: $(adb shell getprop ro.build.version.sdk | tr -d '\r')" >> rehearsal/evidence.txt
echo "Emulator model: $(adb shell getprop ro.product.model | tr -d '\r')" >> rehearsal/evidence.txt

adb install rehearsal/n1.apk | tee rehearsal/install-n1.txt
grep -Fq Success rehearsal/install-n1.txt
adb logcat -c
adb shell monkey -p "$APP_ID" -c android.intent.category.LAUNCHER 1 >/dev/null
wait_for_marker 'IAMINA_P5_UPGRADE_SEED_OK' rehearsal/seed-logcat.txt

PACKAGE_BEFORE="$(adb shell dumpsys package "$APP_ID" | tr -d '\r')"
FIRST_INSTALL="$(printf '%s\n' "$PACKAGE_BEFORE" | sed -n 's/^[[:space:]]*firstInstallTime=//p' | head -1)"
USER_ID="$(printf '%s\n' "$PACKAGE_BEFORE" | sed -n 's/^[[:space:]]*userId=//p' | head -1)"
VERSION_BEFORE="$(printf '%s\n' "$PACKAGE_BEFORE" | sed -n 's/.*versionCode=\([0-9]*\).*/\1/p' | head -1)"
test "$VERSION_BEFORE" = "1"
test -n "$FIRST_INSTALL" && test -n "$USER_ID"

adb install -r rehearsal/n.apk | tee rehearsal/install-n.txt
grep -Fq Success rehearsal/install-n.txt
PACKAGE_AFTER="$(adb shell dumpsys package "$APP_ID" | tr -d '\r')"
VERSION_AFTER="$(printf '%s\n' "$PACKAGE_AFTER" | sed -n 's/.*versionCode=\([0-9]*\).*/\1/p' | head -1)"
FIRST_AFTER="$(printf '%s\n' "$PACKAGE_AFTER" | sed -n 's/^[[:space:]]*firstInstallTime=//p' | head -1)"
UID_AFTER="$(printf '%s\n' "$PACKAGE_AFTER" | sed -n 's/^[[:space:]]*userId=//p' | head -1)"
test "$VERSION_AFTER" = "2"
test "$FIRST_AFTER" = "$FIRST_INSTALL"
test "$UID_AFTER" = "$USER_ID"

adb logcat -c
adb shell am force-stop "$APP_ID"
adb shell monkey -p "$APP_ID" -c android.intent.category.LAUNCHER 1 >/dev/null
wait_for_marker 'IAMINA_P5_UPGRADE_VERIFY_OK' rehearsal/update-logcat.txt

adb root >/dev/null 2>&1 || true
adb wait-for-device
PING_BIN="$(adb shell command -v ping | tr -d '\r')"
test -n "$PING_BIN"
adb shell ping -c 1 -W 2 8.8.8.8 > rehearsal/network-before.txt 2>&1

echo "Network probe command available: PASS" >> rehearsal/evidence.txt
echo "Pre-isolation connectivity: PASS" >> rehearsal/evidence.txt

adb shell svc wifi disable || true
adb shell ip link set eth0 down || true
if adb shell ping -c 1 -W 1 8.8.8.8 > rehearsal/network-after.txt 2>&1; then
  echo "::error::Emulator still has network connectivity"
  exit 1
fi

echo "Post-isolation connectivity blocked: PASS" >> rehearsal/evidence.txt

adb logcat -c
adb shell am force-stop "$APP_ID"
adb shell monkey -p "$APP_ID" -c android.intent.category.LAUNCHER 1 >/dev/null
wait_for_marker 'IAMINA_P5_UPGRADE_VERIFY_OK' rehearsal/offline-logcat.txt

{
  echo "N-1 clean install: PASS"
  echo "N-1 Drift seed: PASS"
  echo "N-1 -> N adb install -r: PASS"
  echo "Package identity preserved: PASS"
  echo "firstInstallTime preserved: PASS"
  echo "userId preserved: PASS"
  echo "Drift logs/profile/medication/reminder preserved: PASS"
  echo "Offline network probe: PASS"
  echo "Offline reopen and Drift verification: PASS"
  echo "Physical-device evidence: NOT PROVEN"
} >> rehearsal/evidence.txt
