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

first_install_time_file() {
  awk '/^[[:space:]]*firstInstallTime=/ {sub(/^[[:space:]]*firstInstallTime=/, ""); print; exit}' "$1"
}

package_user_id_file() {
  awk '/^[[:space:]]*userId=/ {sub(/^[[:space:]]*userId=/, ""); print; exit}' "$1"
}

package_version_code_file() {
  awk 'match($0, /versionCode=[0-9]+/) {value=substr($0, RSTART, RLENGTH); sub(/^versionCode=/, "", value); print value; exit}' "$1"
}

require_equal() {
  local label="$1"
  local actual="$2"
  local expected="$3"
  if [ "$actual" != "$expected" ]; then
    echo "::error::$label expected=$expected actual=${actual:-<empty>}"
    return 1
  fi
}

require_nonempty() {
  local label="$1"
  local actual="$2"
  if [ -z "$actual" ]; then
    echo "::error::$label is empty"
    return 1
  fi
}

echo "Emulator API: $(adb shell getprop ro.build.version.sdk | tr -d '\r')" >> rehearsal/evidence.txt
echo "Emulator model: $(adb shell getprop ro.product.model | tr -d '\r')" >> rehearsal/evidence.txt

adb install rehearsal/n1.apk | tee rehearsal/install-n1.txt
grep -Fq Success rehearsal/install-n1.txt
adb logcat -c
adb shell monkey -p "$APP_ID" -c android.intent.category.LAUNCHER 1 >/dev/null
wait_for_marker 'IAMINA_P5_UPGRADE_SEED_OK' rehearsal/seed-logcat.txt

adb shell dumpsys package "$APP_ID" | tr -d '\r' > rehearsal/package-before.txt
FIRST_INSTALL="$(first_install_time_file rehearsal/package-before.txt)"
USER_ID="$(package_user_id_file rehearsal/package-before.txt)"
VERSION_BEFORE="$(package_version_code_file rehearsal/package-before.txt)"
{
  echo "N-1 observed versionCode: ${VERSION_BEFORE:-<empty>}"
  echo "N-1 observed firstInstallTime: ${FIRST_INSTALL:-<empty>}"
  echo "N-1 observed userId: ${USER_ID:-<empty>}"
} >> rehearsal/evidence.txt
require_equal "N-1 versionCode" "$VERSION_BEFORE" "1"
require_nonempty "N-1 firstInstallTime" "$FIRST_INSTALL"
require_nonempty "N-1 userId" "$USER_ID"

adb install -r rehearsal/n.apk | tee rehearsal/install-n.txt
grep -Fq Success rehearsal/install-n.txt
adb shell dumpsys package "$APP_ID" | tr -d '\r' > rehearsal/package-after.txt
VERSION_AFTER="$(package_version_code_file rehearsal/package-after.txt)"
FIRST_AFTER="$(first_install_time_file rehearsal/package-after.txt)"
UID_AFTER="$(package_user_id_file rehearsal/package-after.txt)"
{
  echo "N observed versionCode: ${VERSION_AFTER:-<empty>}"
  echo "N observed firstInstallTime: ${FIRST_AFTER:-<empty>}"
  echo "N observed userId: ${UID_AFTER:-<empty>}"
} >> rehearsal/evidence.txt
require_equal "N versionCode" "$VERSION_AFTER" "2"
require_equal "firstInstallTime preservation" "$FIRST_AFTER" "$FIRST_INSTALL"
require_equal "userId preservation" "$UID_AFTER" "$USER_ID"

adb logcat -c
adb shell am force-stop "$APP_ID"
adb shell monkey -p "$APP_ID" -c android.intent.category.LAUNCHER 1 >/dev/null
wait_for_marker 'IAMINA_P5_UPGRADE_VERIFY_OK' rehearsal/update-logcat.txt

adb root >/dev/null 2>&1 || true
adb wait-for-device
PING_BIN="$(adb shell command -v ping | tr -d '\r')"
require_nonempty "ping command" "$PING_BIN"
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
