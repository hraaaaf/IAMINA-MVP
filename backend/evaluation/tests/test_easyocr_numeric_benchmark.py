from __future__ import annotations

import base64
import hashlib

from evaluation.easyocr_numeric_benchmark import run_easyocr_numeric_benchmark
from evaluation.misraj_dataset_preflight import summarize_misraj_viewer


_IMAGE_BYTES = b"easyocr-test-image"


def _payload() -> dict[str, object]:
    encoded = base64.b64encode(_IMAGE_BYTES).decode()
    return {
        "features": [
            {"name": "uuid"},
            {"name": "markdown"},
            {"name": "image"},
        ],
        "num_rows_total": 400,
        "rows": [
            {
                "row": {
                    "uuid": "expected-uuid",
                    "markdown": "سكر ٥٤",
                    "image": {"src": f"data:image/png;base64,{encoded}"},
                }
            }
        ],
    }


def _source(payload: dict[str, object]) -> dict[str, object]:
    preflight = summarize_misraj_viewer(
        payload,
        expected_total_rows=400,
        expected_features=["uuid", "markdown", "image"],
        expected_first_uuid="expected-uuid",
    )
    return {
        "expected_total_rows": 400,
        "expected_features": ["uuid", "markdown", "image"],
        "expected_first_uuid": "expected-uuid",
        "expected_sample_fingerprint_sha256": preflight["sample_fingerprint_sha256"],
        "allowed_image_src_hosts": [],
        "expected_image_sha256_by_uuid": {
            "expected-uuid": hashlib.sha256(_IMAGE_BYTES).hexdigest()
        },
    }


def test_easyocr_adapter_reuses_exact_numeric_safety_contract():
    payload = _payload()
    result = run_easyocr_numeric_benchmark(
        payload,
        _source(payload),
        ocr_callable=lambda _: "سكر 54",
    )

    assert result["benchmark"] == "c29-misraj-easyocr-exact-numeric-safety"
    assert result["engine"] == "easyocr"
    assert result["engine_config"] == {
        "languages": ["ar", "en"],
        "gpu": False,
        "paragraph": False,
    }
    assert result["numeric_safe_cases"] == 1
    assert result["numeric_safety_floor_passed"] is True


def test_easyocr_adapter_preserves_negative_verdict():
    payload = _payload()
    result = run_easyocr_numeric_benchmark(
        payload,
        _source(payload),
        ocr_callable=lambda _: "سكر 54 99",
    )

    assert result["numeric_safe_cases"] == 0
    assert result["numeric_safety_floor_passed"] is False
