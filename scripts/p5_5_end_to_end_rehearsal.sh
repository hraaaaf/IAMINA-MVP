#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT_DIR="${IAMINA_P5_5_ARTIFACT_DIR:-${ROOT_DIR}/artifacts/p5-5}"
SUMMARY_FILE="${ARTIFACT_DIR}/rehearsal-summary.txt"
mkdir -p "${ARTIFACT_DIR}"
: > "${SUMMARY_FILE}"

failed=0

record() {
  printf '%s\n' "$1" | tee -a "${SUMMARY_FILE}"
}

run_lane() {
  local label="$1"
  shift
  if flutter test "$@"; then
    record "LANE|${label}|PASS"
  else
    record "LANE|${label}|FAIL"
    failed=1
  fi
}

record_boundary() {
  local label="$1"
  local status="$2"
  local detail="$3"
  record "LANE|${label}|${status}|${detail}"
}

record "P5_5_REHEARSAL_VERSION=2"
record "SOURCE_SHA=${GITHUB_SHA:-local}"
record "EVENT=${GITHUB_EVENT_NAME:-local}"
record "EVIDENCE_CLASS=synthetic-non-patient"
record "REAL_PATIENT_EVIDENCE=false"

cd "${ROOT_DIR}/frontend"

run_lane "onboarding" \
  test/p0_localized_onboarding_contract_test.dart \
  test/p0_localized_onboarding_copy_contract_test.dart

run_lane "data-import" \
  test/document_ingest_minimizer_test.dart \
  test/document_upload_preflight_test.dart \
  test/p0_mobile_import_navigation_test.dart

run_lane "companion" \
  test/companion_screen_test.dart \
  test/features/chat/amina_chat_view_test.dart \
  test/services/companion_service_chat_test.dart

record_boundary "ocr-arabic-full-document-primary" "QUALIFIED_NEGATIVE" "P5-2 retained real-camera evidence does not qualify local Arabic full-document OCR as primary"

run_lane "cgm" \
  test/services/cgm_service_test.dart \
  test/features/cgm_product_wiring_contract_test.dart \
  test/features/cgm_how_to_use_contract_test.dart

run_lane "reports-pdf" \
  test/services/local_report_pdf_test.dart

run_lane "offline-sync" \
  test/services/connectivity_test.dart \
  test/services/sync_service_test.dart \
  test/services/context_intelligence_sync_test.dart

record_boundary "update-physical-install" "EXTERNAL" "P5-4 signed artifact and real-device upgrade evidence remain separate human/device gates"

run_lane "backup-restore" \
  test/data/drift/local_backup_restore_test.dart

run_lane "degraded-modes" \
  test/ux_4_summary_degraded_contract_test.dart \
  test/services/provider_api_error_test.dart

record_boundary "physical-android-device" "EXTERNAL" "not certified by synthetic GitHub runner"
record_boundary "live-physical-cgm-sensor" "EXTERNAL" "not certified by synthetic GitHub runner"
record_boundary "production-signing-distribution" "EXTERNAL" "not certified by synthetic GitHub runner"

if [[ "${failed}" -ne 0 ]]; then
  record "P5_5_RESULT=FAIL"
  exit 1
fi

record "P5_5_RESULT=PASS_WITH_BOUNDARIES"
