from __future__ import annotations

import base64
import hashlib
from io import BytesIO

from PIL import Image

from evaluation.misraj_dataset_preflight import summarize_misraj_viewer
from evaluation.paddleocr_vl16_numeric_benchmark import (
    PADDLEOCR_VL_MODEL_REVISION,
    make_paddleocr_vl16_callable,
    run_paddleocr_vl16_numeric_benchmark,
)

_IMAGE_BYTES = b"paddleocr-vl16-test-image"


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


def test_paddleocr_vl16_adapter_extracts_markdown_text():
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="PNG")

    class Result:
        markdown = {"markdown_texts": "سكر ٥٤\n68"}

    class Pipeline:
        def predict(self, image_path: str):
            with Image.open(image_path) as image:
                assert image.mode == "RGB"
            return [Result()]

    ocr = make_paddleocr_vl16_callable(pipeline_factory=Pipeline)
    assert ocr(buffer.getvalue()) == "سكر ٥٤\n68"


def test_paddleocr_vl16_adapter_accepts_markdown_text_list():
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="PNG")

    class Result:
        markdown = {"markdown_texts": ["سكر ٥٤", "68"]}

    class Pipeline:
        def predict(self, image_path: str):
            return [Result()]

    ocr = make_paddleocr_vl16_callable(pipeline_factory=Pipeline)
    assert ocr(buffer.getvalue()) == "سكر ٥٤\n68"


def test_paddleocr_vl16_reuses_exact_numeric_safety_contract():
    payload = _payload()
    result = run_paddleocr_vl16_numeric_benchmark(
        payload,
        _source(payload),
        ocr_callable=lambda _: "سكر 54",
    )

    assert result["benchmark"] == "c31-misraj-paddleocr-vl16-exact-numeric-safety"
    assert result["engine"] == "paddleocr-vl-1.6"
    assert result["engine_config"]["package_version"] == "3.7.0"
    assert result["engine_config"]["pipeline_version"] == "v1.6"
    assert result["engine_config"]["model_revision"] == PADDLEOCR_VL_MODEL_REVISION
    assert result["engine_config"]["device"] == "cpu"
    assert result["numeric_safe_cases"] == 1
    assert result["numeric_safety_floor_passed"] is True


def test_paddleocr_vl16_preserves_negative_verdict():
    payload = _payload()
    result = run_paddleocr_vl16_numeric_benchmark(
        payload,
        _source(payload),
        ocr_callable=lambda _: "سكر 54 99",
    )

    assert result["numeric_safe_cases"] == 0
    assert result["numeric_safety_floor_passed"] is False
