#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVIDENCE="$ROOT/artifacts/d7-d9-two-emulators"
mkdir -p "$EVIDENCE"
SECOND_PID=""
HUB_PID=""
cleanup() {
  if [ -n "$HUB_PID" ]; then kill "$HUB_PID" 2>/dev/null || true; fi
  if [ -n "$SECOND_PID" ]; then kill "$SECOND_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT

: "$ANDROID_HOME"
test -c /dev/kvm
adb -s emulator-5554 get-state | grep -Fx device
python3 "$ROOT/scripts/ci_d7_d9_emulator_hub.py" \
  --output "$EVIDENCE/shared-hub.json" &
HUB_PID=$!
printf 'no\n' | avdmanager create avd --name iamina-ci-device-two \
  --package 'system-images;android-35;google_apis;x86_64' \
  --device pixel_5 --force
"$ANDROID_HOME/emulator/emulator" -avd iamina-ci-device-two \
  -port 5556 -no-window -no-audio -no-boot-anim \
  -no-snapshot -gpu swiftshader_indirect -memory 1536 -cores 2 \
  >"$EVIDENCE/emulator-two-boot.log" 2>&1 &
SECOND_PID=$!

adb -s emulator-5556 wait-for-device
timeout 420 bash -c '
  until [ "$(adb -s emulator-5556 shell getprop sys.boot_completed | tr -d "\r")" = 1 ]; do
    sleep 3
  done
'
for serial in emulator-5554 emulator-5556; do
  adb -s "$serial" get-state | grep -Fx device
  adb -s "$serial" reverse tcp:8765 tcp:8765
  adb -s "$serial" shell settings put global window_animation_scale 0
  adb -s "$serial" shell settings put global transition_animation_scale 0
  adb -s "$serial" shell settings put global animator_duration_scale 0
  echo "$serial Android=$(adb -s "$serial" shell getprop ro.build.version.release | tr -d '\r')" \
    >>"$EVIDENCE/device-inventory.txt"
done
adb devices -l | tee "$EVIDENCE/adb-devices.txt"
test "$(adb devices | grep -Ec '^emulator-(5554|5556)[[:space:]]+device$')" -eq 2

cd "$ROOT/frontend"
flutter test integration_test/d7_d9_ubuntu_two_emulators_test.dart \
  -d emulator-5554 \
  --dart-define=IAMINA_VIRTUAL_DEVICE_ROLE=device-one \
  --dart-define=ENABLE_FIREBASE_MIGRATION=false \
  | tee "$EVIDENCE/device-one-test.txt"
flutter test integration_test/d7_d9_ubuntu_two_emulators_test.dart \
  -d emulator-5556 \
  --dart-define=IAMINA_VIRTUAL_DEVICE_ROLE=device-two \
  --dart-define=ENABLE_FIREBASE_MIGRATION=false \
  | tee "$EVIDENCE/device-two-test.txt"

python3 - "$EVIDENCE/shared-hub.json" <<'PY'
import json
from pathlib import Path
import sys
obj = json.loads(Path(sys.argv[1]).read_text())
assert obj['attestations'] == {
    'device-one': 'same-install-a-b-a-cold-restart',
    'device-two': 'fresh-install-no-remote-restore',
}
assert obj['physical_devices_tested'] is False
assert obj['remote_profile_restored'] is False
assert obj['clinical_egress_certified'] is False
print('PASS: two distinct Android emulators connected to ONE synthetic Ubuntu hub')
PY
