#!/usr/bin/env bash
set -u -o pipefail

OUT="${1:-artifacts/p5-5-rehearsal.txt}"
mkdir -p "$(dirname "$OUT")"
TESTED_SHA="$(git rev-parse HEAD)"
SOURCE_HEAD_SHA="${SOURCE_HEAD_SHA:-$TESTED_SHA}"
FAILURES=0

cat >"$OUT" <<EOF
IAMINA P5-5 END-TO-END PILOT REHEARSAL
tested_sha=$TESTED_SHA
source_head_sha=$SOURCE_HEAD_SHA
patient_data=false
fixture_class=synthetic_only
proof_type=automated_engineering

LANE | STATUS | PROOF
EOF

record() {
  printf '%s | %s | %s\n' "$1" "$2" "$3" >>"$OUT"
}

run_lane() {
  local lane="$1"
  local proof="$2"
  shift 2
  if "$@"; then
    record "$lane" "PASS" "$proof"
  else
    record "$lane" "FAIL" "$proof"
    FAILURES=$((FAILURES + 1))
  fi
}

run_lane \
  "static-analysis" \
  "flutter analyze --no-fatal-infos" \
  bash -lc 'cd frontend && flutter analyze --no-fatal-infos'

run_lane \
  "onboarding" \
  "localized onboarding + consent contracts" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/p0_localized_onboarding_contract_test.dart test/features/auth/consent_screen_test.dart test/services/consent_service_test.dart'

run_lane \
  "manual-data-entry" \
  "synthetic glucose/context/meal/insulin/medication contracts" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/features/add_log_sheet_test.dart test/features/insulin_logging_v2_test.dart test/features/meal_capture_panel_test.dart test/features/medication_screen_test.dart test/features/reminders_truthfulness_contract_test.dart'

run_lane \
  "document-import-ocr" \
  "synthetic import truthfulness + local Latin OCR smoke + OCR route/shield contracts; Arabic full-document primary remains UNQUALIFIED" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/document_ingest_minimizer_test.dart test/features/document_import_truthfulness_contract_test.dart test/features/importer_truthfulness_contract_test.dart; cd ..; python scripts/run_local_ocr_smoke.py --output /tmp/p5-5-local-ocr-smoke.json >/tmp/p5-5-local-ocr-smoke.log; cd backend; pytest diabetes/tests/test_ocr_route_runtime.py diabetes/tests/test_pulper_security.py -q'

run_lane \
  "companion" \
  "frontend truthfulness + deterministic zero-model/output guard contracts" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/companion_screen_test.dart test/features/companion_uncertainty_copy_contract_test.dart; cd ../backend; pytest companion/test_output_guard.py companion/test_zero_model_router.py companion/test_zero_model_runtime.py -q'

run_lane \
  "cgm" \
  "synthetic/provenance gateway contracts; live physical sensor not claimed" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/services/cgm_service_test.dart test/features/cgm_product_wiring_contract_test.dart; cd ../backend; pytest diabetes/tests/test_cgm_product_e2e.py integrations/cgm/tests/test_nightscout.py -q'

run_lane \
  "reports-export" \
  "deterministic local PDF bytes + summary truthfulness; UI share/print and Unicode PDF not claimed" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/services/local_report_pdf_test.dart test/features/summary_truthfulness_contract_test.dart'

run_lane \
  "offline" \
  "connectivity/sync contracts plus retained emulator prerequisite run 33440140316; physical device not claimed" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/services/connectivity_test.dart test/services/sync_service_test.dart'

run_lane \
  "update" \
  "Drift N-1 to N migration contract plus retained emulator prerequisite run 33440140316; production signing not claimed" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/data/drift/pilot_release_v9_to_v10_migration_test.dart'

run_lane \
  "backup-restore" \
  "versioned five-table Drift round trip + transactional rollback on invalid backup" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/data/drift/local_backup_restore_test.dart'

run_lane \
  "degraded-modes" \
  "provider/network/Companion/summary/import failures remain explicit and bounded" \
  bash -lc 'set -euo pipefail; cd frontend; flutter test --no-pub test/services/provider_api_error_test.dart test/services/connectivity_test.dart test/features/companion_uncertainty_copy_contract_test.dart test/ux_4_summary_degraded_contract_test.dart test/features/document_import_truthfulness_contract_test.dart'

cat >>"$OUT" <<'EOF'

EXTERNAL / NEGATIVE QUALIFICATION BOUNDARIES
BOUNDARY | STATUS | EVIDENCE
physical-android-device | NOT_PROVEN | P5-4 evidence is emulator-only
live-physical-cgm-sensor | NOT_PROVEN | synthetic/provenance fixtures only
production-signing-lineage | NOT_PROVEN | P5-4 cloud rehearsal does not prove production signing
arabic-local-full-document-primary | UNQUALIFIED | retained P5-2 negative qualification remains authoritative
report-unicode-arabic-pdf | NOT_QUALIFIED | export fails closed outside printable ASCII instead of corrupting content
real-patient-use | NOT_PROVEN | explicitly outside this synthetic rehearsal
vercel-deployment | NOT_PERFORMED | outside P5-5 and not authorized
EOF

if [[ "$FAILURES" -eq 0 ]]; then
  record "overall-machine-rehearsal" "PASS" "all mandatory machine-testable lanes passed on exact tested/source SHA pair"
else
  record "overall-machine-rehearsal" "FAIL" "$FAILURES mandatory machine-testable lane(s) failed"
fi

cat "$OUT"
exit "$FAILURES"
