"""PaddleOCR-VL 1.6 adapter for the pinned Misraj numeric-safety benchmark.

Preparation only: the heavyweight benchmark workflow is intentionally not
created until C30 Surya2 has returned evidence. Runtime model downloads are
forbidden here; C31 must receive a separately pinned local model directory.
"""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image, ImageOps

from evaluation.misraj_numeric_benchmark import run_misraj_numeric_benchmark


PADDLEOCR_PACKAGE_VERSION = "3.7.0"
PADDLEOCR_VL_PIPELINE_VERSION = "v1.6"
PADDLEOCR_VL_MODEL = "PaddlePaddle/PaddleOCR-VL-1.6"
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


def _markdown_text(result: object) -> str:
    markdown = result.get("markdown") if isinstance(result, dict) else getattr(result, "markdown", None)
    if not isinstance(markdown, dict):
        raise ValueError("PaddleOCR-VL result must expose markdown data")

    value = markdown.get("markdown_texts")
    if value is None:
        value = markdown.get("text")
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return "\n".join(value)
    raise ValueError("PaddleOCR-VL markdown text is missing")


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
        return _markdown_text(results[0]).strip()

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
        "model_sha256": PADDLEOCR_VL_MODEL_SHA256,
        "engine": "transformers",
        "device": "cpu",
        "layout_detection": False,
        "full_page": True,
    }
    return result
