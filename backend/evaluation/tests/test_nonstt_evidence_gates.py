import hashlib
import json
from pathlib import Path

import pytest

from evaluation.media_fixture_manifest import MediaFixtureError, validate_media_fixture_manifest
from evaluation.provider_benchmark_preflight import (
    ProviderBenchmarkBlocked,
    ProviderBenchmarkPreflight,
)
from evaluation.tts_device_evidence import (
    TTSDeviceEvidenceError,
    TTSDeviceObservation,
    summarize_device_tts_evidence,
)


def test_provider_preflight_blocks_without_explicit_network_authorization():
    preflight = ProviderBenchmarkPreflight(
        provider="controlled-provider",
        model="exact-model-id",
        modality="text",
        dataset_id="synthetic-text-v1",
        credential_reference="env:CONTROLLED_API_KEY",
        pricing_evidence_reference="pricing-record-2026-08-19",
        network_authorized=False,
        spend_ceiling_microusd=100_000,
        patient_data=False,
    )

    with pytest.raises(ProviderBenchmarkBlocked, match="authorization"):
        preflight.validate()


def test_provider_preflight_accepts_complete_contract_without_invoking_network():
    preflight = ProviderBenchmarkPreflight(
        provider="controlled-provider",
        model="exact-model-id",
        modality="text",
        dataset_id="synthetic-text-v1",
        credential_reference="env:CONTROLLED_API_KEY",
        pricing_evidence_reference="pricing-record-2026-08-19",
        network_authorized=True,
        spend_ceiling_microusd=100_000,
        patient_data=False,
    )

    preflight.validate()


def _tts(locale: str, *, adequate: bool = True) -> TTSDeviceObservation:
    return TTSDeviceObservation(
        case_id=f"eval_tts_{locale.replace('-', '_')}",
        locale=locale,
        platform="ios",
        os_version="controlled-test-os",
        device_model="controlled-test-device",
        engine="native",
        voice="system-default",
        human_checked=True,
        intelligible=adequate,
        critical_content_preserved=adequate,
        patient_data=False,
    )


def test_tts_device_evidence_requires_human_check_and_reports_failure_without_hiding_it():
    summary = summarize_device_tts_evidence(
        (_tts("fr-FR"), _tts("ar-MA", adequate=False)),
        required_locales=("fr-FR", "ar-MA"),
    )
    assert summary["all_adequate"] is False

    with pytest.raises(TTSDeviceEvidenceError, match="human_checked"):
        summarize_device_tts_evidence(
            (_tts("fr-FR"), _tts("ar-MA").__class__(
                **{**_tts("ar-MA").__dict__, "human_checked": False}
            )),
            required_locales=("fr-FR", "ar-MA"),
        )


def _write_media_manifest(tmp_path: Path, entries: list[dict]) -> Path:
    manifest = tmp_path / "media.json"
    manifest.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    return manifest


def test_media_fixture_manifest_accepts_integrity_pinned_arabic_real_camera_fixture(tmp_path):
    image = tmp_path / "fixtures" / "arabic.jpg"
    image.parent.mkdir()
    image.write_bytes(b"controlled-nonpatient-camera-image")
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    manifest = _write_media_manifest(
        tmp_path,
        [
            {
                "fixture_id": "ocr_ar_camera_01",
                "image_fixture": "fixtures/arabic.jpg",
                "image_sha256": digest,
                "source_type": "real_camera_test",
                "patient_data": False,
                "locale": "ar-MA",
                "reference_text": "سكر الدم 54 mg/dL",
                "capture_profile": "handheld_indoor",
                "capture_device": "controlled-test-phone",
            }
        ],
    )

    assert len(validate_media_fixture_manifest(manifest, tmp_path)) == 1


def test_media_fixture_manifest_rejects_patient_data_and_tampering(tmp_path):
    image = tmp_path / "fixture.png"
    image.write_bytes(b"controlled-image")
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    base = {
        "fixture_id": "ocr_ar_01",
        "image_fixture": "fixture.png",
        "image_sha256": digest,
        "source_type": "synthetic_render",
        "patient_data": False,
        "locale": "ar-MA",
        "reference_text": "سكر الدم 54 mg/dL",
        "capture_profile": "synthetic",
    }

    with pytest.raises(MediaFixtureError, match="patient_data"):
        validate_media_fixture_manifest(
            _write_media_manifest(tmp_path, [{**base, "patient_data": True}]),
            tmp_path,
        )

    with pytest.raises(MediaFixtureError, match="SHA-256 mismatch"):
        validate_media_fixture_manifest(
            _write_media_manifest(tmp_path, [{**base, "image_sha256": "0" * 64}]),
            tmp_path,
        )
