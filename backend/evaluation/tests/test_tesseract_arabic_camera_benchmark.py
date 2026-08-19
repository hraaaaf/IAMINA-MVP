from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from evaluation.tesseract_arabic_camera_benchmark import (
    ArabicCameraBenchmarkError,
    extract_numeric_tokens,
    run_tesseract_arabic_camera_benchmark,
)


def _write_manifest(
    tmp_path: Path,
    *,
    reference_text: str = "سكر الدم 54",
    source_type: str = "real_camera_test",
    locale: str = "ar-MA",
) -> tuple[Path, Path]:
    image = tmp_path / "fixtures" / "arabic-camera.jpg"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b"controlled-nonpatient-arabic-camera-fixture")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "fixture_id": "ocr_ar_camera_01",
                    "image_fixture": "fixtures/arabic-camera.jpg",
                    "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                    "source_type": source_type,
                    "patient_data": False,
                    "locale": locale,
                    "reference_text": reference_text,
                    "capture_profile": "handheld_indoor",
                    "capture_device": "controlled-test-phone",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return manifest, image


def test_numeric_token_normalization_accepts_arabic_indic_digits_and_decimal_separator():
    assert extract_numeric_tokens("سكر ٥٤ والتراكمي ٧٫٤") == ("54", "7.4")


def test_real_camera_benchmark_passes_exact_numeric_safety_with_arabic_indic_output(tmp_path):
    manifest, _ = _write_manifest(tmp_path, reference_text="السكر التراكمي 7.4")

    result = run_tesseract_arabic_camera_benchmark(
        manifest,
        tmp_path,
        ocr_callable=lambda _: "السكر التراكمي ٧٫٤",
        engine_version="tesseract-test",
    )

    assert result["numeric_safe_cases"] == 1
    assert result["numeric_total"] == 1
    assert result["numeric_safety_floor_passed"] is True
    assert result["cases"][0]["expected_numeric_tokens"] == ("7.4",)
    assert result["cases"][0]["extracted_numeric_tokens"] == ("7.4",)


def test_real_camera_benchmark_rejects_numeric_substring_false_positive(tmp_path):
    manifest, _ = _write_manifest(tmp_path, reference_text="سكر الدم 54")

    result = run_tesseract_arabic_camera_benchmark(
        manifest,
        tmp_path,
        ocr_callable=lambda _: "سكر الدم 154",
        engine_version="tesseract-test",
    )

    assert result["numeric_safety_floor_passed"] is False
    assert result["cases"][0]["expected_numeric_tokens"] == ("54",)
    assert result["cases"][0]["extracted_numeric_tokens"] == ("154",)


def test_real_camera_benchmark_rejects_extra_numeric_token(tmp_path):
    manifest, _ = _write_manifest(tmp_path, reference_text="سكر الدم 54")

    result = run_tesseract_arabic_camera_benchmark(
        manifest,
        tmp_path,
        ocr_callable=lambda _: "سكر الدم 54 154",
        engine_version="tesseract-test",
    )

    assert result["numeric_safety_floor_passed"] is False
    assert result["cases"][0]["expected_numeric_tokens"] == ("54",)
    assert result["cases"][0]["extracted_numeric_tokens"] == ("54", "154")


def test_real_camera_benchmark_rejects_synthetic_or_non_arabic_fixtures(tmp_path):
    synthetic_manifest, _ = _write_manifest(tmp_path, source_type="synthetic_render")
    with pytest.raises(ArabicCameraBenchmarkError, match="real_camera_test"):
        run_tesseract_arabic_camera_benchmark(
            synthetic_manifest,
            tmp_path,
            ocr_callable=lambda _: "سكر الدم 54",
            engine_version="tesseract-test",
        )

    arabic_manifest, _ = _write_manifest(tmp_path, locale="fr-FR")
    with pytest.raises(ArabicCameraBenchmarkError, match="Arabic locale"):
        run_tesseract_arabic_camera_benchmark(
            arabic_manifest,
            tmp_path,
            ocr_callable=lambda _: "سكر الدم 54",
            engine_version="tesseract-test",
        )


def test_real_camera_benchmark_requires_numeric_safety_token(tmp_path):
    manifest, _ = _write_manifest(tmp_path, reference_text="سكر الدم")

    with pytest.raises(ArabicCameraBenchmarkError, match="no numeric safety token"):
        run_tesseract_arabic_camera_benchmark(
            manifest,
            tmp_path,
            ocr_callable=lambda _: "سكر الدم",
            engine_version="tesseract-test",
        )
