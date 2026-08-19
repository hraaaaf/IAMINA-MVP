"""PaddleOCR-VL 1.6 adapter for the pinned Misraj numeric-safety benchmark.

Benchmark-only. The model must be materialized from the pinned Hugging Face
revision before execution; implicit runtime model downloads are forbidden.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image, ImageOps

from evaluation.misraj_numeric_benchmark import run_misraj_numeric_benchmark

PADDLEOCR_PACKAGE_VERSION = "3.7.0"
PADDLEOCR_VL_PIPELINE_VERSION = "v1.6"
PADDLEOCR_VL_MODEL = "PaddlePaddle/PaddleOCR-VL-1.6"
PADDLEOCR_VL_MODEL_REVISION = "c5630abae1d940eafe0697512a0325494b02ab42"
PADDLEOCR_VL_MODEL_SHA256 = "85a479d506a11e724e7285d395c551be69f41dbc16b6342d3cacfb189aed71db"

PipelineFactory = Callable[[], Any]
OCRCallable = Callable[[bytes], str]


def _default_pipeline_factory() -> Any:
    model_dir = os.getenv("C31_PADDLEOCR_VL_MODEL_DIR")
    if not model_dir:
        raise RuntimeError("C31 requires C31_PADDLEOCR_VL_MODEL_DIR")
    path = Path(model_dir)
    if not path.is_dir():
        raise RuntimeError("C31 pinned PaddleOCR-VL model directory is missing")

    from paddleocr import PaddleOCRVL

    return PaddleOCRVL(
        pipeline_version=PADDLEOCR_VL_PIPELINE_VERSION,
        vl_rec_model_dir=str(path),
        use_layout_detection=False,
        device="cpu",
        engine="transformers",
    )


def _result_text(result: object) -> str:
    """Extract text from PaddleOCR-VL's canonical parsing_res_list contract."""
    parsing_res_list = None
    if isinstance(result, dict):
        parsing_res_list = result.get("parsing_res_list")
    else:
        getter = getattr(result, "get", None)
        if callable(getter):
            parsing_res_list = getter("parsing_res_list")
        if parsing_res_list is None:
            parsing_res_list = getattr(result, "parsing_res_list", None)

    if not isinstance(parsing_res_list, list):
        raise ValueError("PaddleOCR-VL result must expose parsing_res_list")

    chunks: list[str] = []
    for block in parsing_res_list:
        if isinstance(block, dict):
            value = block.get("block_content")
            if value is None:
                value = block.get("content")
        else:
            value = getattr(block, "content", None)
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())

    if not chunks:
        raise ValueError("PaddleOCR-VL parsing_res_list contains no text")
    return "\n".join(chunks)


def make_paddleocr_vl16_callable(
    *,
    pipeline_factory: PipelineFactory = _default_pipeline_factory,
) -> OCRCallable:
    pipeline = pipeline_factory()

    def ocr(image_bytes: bytes) -> str:
        with TemporaryDirectory(prefix="iamina-c31-") as tmp:
            image_path = Path(tmp) / "page.png"
            with Image.open(BytesIO(image_bytes)) as image:
                normalized = ImageOps.exif_transpose(image).convert("RGB")
                normalized.save(image_path, format="PNG")
            results = list(pipeline.predict(str(image_path)))
        if len(results) != 1:
            raise ValueError("PaddleOCR-VL must return exactly one page result")
        return _result_text(results[0]).strip()

    return ocr


def run_paddleocr_vl16_numeric_benchmark(
    payload: dict[str, Any],
    source: dict[str, Any],
    *,
    ocr_callable: OCRCallable | None = None,
) -> dict[str, object]:
    result = run_misraj_numeric_benchmark(
        payload,
        source,
        ocr_callable=ocr_callable or make_paddleocr_vl16_callable(),
    )
    result["benchmark"] = "c31-misraj-paddleocr-vl16-exact-numeric-safety"
    result["engine"] = "paddleocr-vl-1.6"
    result["engine_config"] = {
        "package": "paddleocr",
        "package_version": PADDLEOCR_PACKAGE_VERSION,
        "pipeline_version": PADDLEOCR_VL_PIPELINE_VERSION,
        "model": PADDLEOCR_VL_MODEL,
        "model_revision": PADDLEOCR_VL_MODEL_REVISION,
        "model_sha256": PADDLEOCR_VL_MODEL_SHA256,
        "engine": "transformers",
        "device": "cpu",
        "layout_detection": False,
        "full_page": True,
    }
    return result
