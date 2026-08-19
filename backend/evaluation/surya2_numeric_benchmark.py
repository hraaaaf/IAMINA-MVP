"""Surya 2 adapter for the C27 pinned exact numeric-safety benchmark.

This adapter is benchmark-only. It does not add Surya to IAMINA runtime
requirements and intentionally emits no raw ground-truth or OCR text.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from html.parser import HTMLParser
from io import BytesIO
from typing import Any

from PIL import Image, ImageOps

from evaluation.misraj_numeric_benchmark import run_misraj_numeric_benchmark


SURYA_PACKAGE_VERSION = "0.22.1"
SURYA_MODEL_REPO = "datalab-to/surya-ocr-2-gguf"
SURYA_MODEL_SHA256 = "1f18abe17b1ed8b4e47ee9b1ad0e274c93daf5efbb6b29a04ff1712e37051e05"
SURYA_MMPROJ_SHA256 = "98c0563673b1657ff6d021d1e5f04af06cbf61bb40c63ac613e8bb71b42fb2c0"

PredictorFactory = Callable[[], Any]
OCRCallable = Callable[[bytes], str]


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)


def _html_to_text(value: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(value)
    parser.close()
    return " ".join(parser.parts)


def _default_predictor_factory() -> Any:
    from surya.inference import SuryaInferenceManager
    from surya.recognition import RecognitionPredictor

    manager = SuryaInferenceManager(method="llamacpp")
    return RecognitionPredictor(manager)


def _block_html(block: object) -> str:
    if isinstance(block, dict):
        value = block.get("html")
    else:
        value = getattr(block, "html", None)
    if not isinstance(value, str):
        raise ValueError("Surya OCR block must expose HTML text")
    return value


def make_surya2_callable(
    *,
    predictor_factory: PredictorFactory = _default_predictor_factory,
) -> OCRCallable:
    predictor = predictor_factory()

    def ocr(image_bytes: bytes) -> str:
        with Image.open(BytesIO(image_bytes)) as image:
            normalized = ImageOps.exif_transpose(image).convert("RGB")
            predictions = predictor([normalized])

        if not isinstance(predictions, list) or len(predictions) != 1:
            raise ValueError("Surya OCR must return exactly one page result")
        page = predictions[0]
        blocks = page.get("blocks") if isinstance(page, dict) else getattr(page, "blocks", None)
        if not isinstance(blocks, list):
            raise ValueError("Surya OCR page must expose ordered blocks")

        text_blocks: list[str] = []
        for block in blocks:
            html = _block_html(block)
            if not html:
                continue
            text = _html_to_text(html)
            if text:
                text_blocks.append(text)
        return "\n".join(text_blocks)

    return ocr


def run_surya2_numeric_benchmark(
    payload: dict[str, Any],
    source: dict[str, Any],
    *,
    ocr_callable: OCRCallable | None = None,
) -> dict[str, object]:
    result = run_misraj_numeric_benchmark(
        payload,
        source,
        ocr_callable=ocr_callable or make_surya2_callable(),
    )
    result["benchmark"] = "c30-misraj-surya2-exact-numeric-safety"
    result["engine"] = "surya2"
    result["engine_config"] = {
        "package": "surya-ocr",
        "package_version": SURYA_PACKAGE_VERSION,
        "model_repo": SURYA_MODEL_REPO,
        "model_sha256": SURYA_MODEL_SHA256,
        "mmproj_sha256": SURYA_MMPROJ_SHA256,
        "backend": "llamacpp",
        "llama_cpp_release": os.getenv("C30_LLAMA_CPP_RELEASE", "unrecorded"),
        "llama_cpp_sha256": os.getenv("C30_LLAMA_CPP_SHA256", "unrecorded"),
        "full_page": True,
    }
    return result
