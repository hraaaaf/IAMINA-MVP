"""Controlled real-camera Arabic OCR benchmark for Tesseract.

The benchmark is intentionally narrow: it validates fixture provenance first and
uses exact numeric-token preservation as a hard safety floor. Passing this module
is not a full OCR adequacy or production-readiness claim.
"""

from __future__ import annotations

import re
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from evaluation.media_fixture_manifest import validate_media_fixture_manifest


class ArabicCameraBenchmarkError(ValueError):
    pass


OCRCallable = Callable[[Path], str]

_DIGIT_TRANSLATION = str.maketrans(
    {
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
        "۰": "0",
        "۱": "1",
        "۲": "2",
        "۳": "3",
        "۴": "4",
        "۵": "5",
        "۶": "6",
        "۷": "7",
        "۸": "8",
        "۹": "9",
    }
)
_NUMBER_RE = re.compile(r"(?<!\d)\d+(?:\.\d+)?(?!\d)")


def extract_numeric_tokens(value: str) -> tuple[str, ...]:
    normalized = (
        value.translate(_DIGIT_TRANSLATION)
        .replace("\u066b", ".")
        .replace(",", ".")
    )
    return tuple(_NUMBER_RE.findall(normalized))


def _tesseract_ocr(path: Path, *, tesseract_bin: str) -> str:
    result = subprocess.run(
        [tesseract_bin, str(path), "stdout", "-l", "ara", "--psm", "6"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _tesseract_version(*, tesseract_bin: str) -> str:
    result = subprocess.run(
        [tesseract_bin, "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()[0]


def run_tesseract_arabic_camera_benchmark(
    manifest_path: Path,
    repo_root: Path,
    *,
    ocr_callable: OCRCallable | None = None,
    engine_version: str | None = None,
    tesseract_bin: str = "tesseract",
) -> dict[str, object]:
    fixtures = validate_media_fixture_manifest(manifest_path, repo_root)
    root = repo_root.resolve()
    ocr = ocr_callable or (lambda path: _tesseract_ocr(path, tesseract_bin=tesseract_bin))
    version = engine_version or _tesseract_version(tesseract_bin=tesseract_bin)

    cases: list[dict[str, object]] = []
    for item in fixtures:
        if item["source_type"] != "real_camera_test":
            raise ArabicCameraBenchmarkError(
                "C24 requires source_type=real_camera_test for every fixture"
            )
        locale = str(item["locale"])
        if not locale.lower().startswith("ar"):
            raise ArabicCameraBenchmarkError("C24 requires an Arabic locale")

        reference = str(item["reference_text"])
        expected_numbers = extract_numeric_tokens(reference)
        if not expected_numbers:
            raise ArabicCameraBenchmarkError(
                f"fixture {item['fixture_id']} has no numeric safety token"
            )

        image_path = root / str(item["image_fixture"])
        started = time.perf_counter()
        extracted = ocr(image_path)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        extracted_numbers = extract_numeric_tokens(extracted)
        numeric_ok = extracted_numbers == expected_numbers
        cases.append(
            {
                "fixture_id": item["fixture_id"],
                "image_fixture": item["image_fixture"],
                "locale": locale,
                "capture_profile": item["capture_profile"],
                "capture_device": item["capture_device"],
                "reference_text": reference,
                "extracted": extracted,
                "expected_numeric_tokens": expected_numbers,
                "extracted_numeric_tokens": extracted_numbers,
                "numeric_ok": numeric_ok,
                "latency_ms": latency_ms,
            }
        )

    numeric_safe_cases = sum(1 for case in cases if case["numeric_ok"])
    return {
        "engine": "tesseract",
        "engine_version": version,
        "language": "ara",
        "benchmark": "c24-controlled-real-camera-arabic-numeric-safety",
        "patient_data": False,
        "provider_api": False,
        "paid_inference": False,
        "real_camera_only": True,
        "numeric_safe_cases": numeric_safe_cases,
        "numeric_total": len(cases),
        "numeric_safety_floor_passed": numeric_safe_cases == len(cases),
        "cases": cases,
    }
