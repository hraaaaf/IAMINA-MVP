from __future__ import annotations

import base64

import pytest

from evaluation.misraj_dataset_preflight import summarize_misraj_viewer
from evaluation.misraj_numeric_benchmark import (
    MisrajNumericBenchmarkError,
    load_viewer_image_bytes,
    run_misraj_numeric_benchmark,
)


def _payload() -> dict[str, object]:
    encoded = base64.b64encode(b"image-bytes").decode()
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
    }


def test_c27_passes_exact_arabic_indic_numeric_token():
    payload = _payload()
    result = run_misraj_numeric_benchmark(
        payload,
        _source(payload),
        ocr_callable=lambda _: "سكر 54",
    )

    assert result["numeric_safe_cases"] == 1
    assert result["numeric_safety_floor_passed"] is True
    assert result["cases"][0]["expected_numeric_tokens"] == ("54",)
    assert result["cases"][0]["extracted_numeric_tokens"] == ("54",)


def test_c27_fails_extra_numeric_token():
    payload = _payload()
    result = run_misraj_numeric_benchmark(
        payload,
        _source(payload),
        ocr_callable=lambda _: "سكر 54 99",
    )

    assert result["numeric_safety_floor_passed"] is False
    assert result["cases"][0]["extracted_numeric_tokens"] == ("54", "99")


def test_c27_requires_pinned_fingerprint_and_hosts():
    payload = _payload()
    source = _source(payload)
    source.pop("expected_sample_fingerprint_sha256")
    with pytest.raises(MisrajNumericBenchmarkError, match="fingerprint"):
        run_misraj_numeric_benchmark(payload, source, ocr_callable=lambda _: "54")

    source = _source(payload)
    source.pop("allowed_image_src_hosts")
    with pytest.raises(MisrajNumericBenchmarkError, match="source hosts"):
        run_misraj_numeric_benchmark(payload, source, ocr_callable=lambda _: "54")


def test_https_image_source_requires_pinned_host():
    image = {"src": "https://datasets-server.huggingface.co/assets/example.png"}
    with pytest.raises(MisrajNumericBenchmarkError, match="not pinned"):
        load_viewer_image_bytes(image, allowed_hosts={"example.com"})

    assert load_viewer_image_bytes(
        image,
        allowed_hosts={"datasets-server.huggingface.co"},
        image_fetcher=lambda _: b"downloaded",
    ) == b"downloaded"
