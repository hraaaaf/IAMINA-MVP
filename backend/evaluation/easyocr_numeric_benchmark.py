"""EasyOCR adapter for the C27 pinned exact numeric-safety benchmark."""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from typing import Any

from PIL import Image, ImageOps

from evaluation.misraj_numeric_benchmark import run_misraj_numeric_benchmark


ReaderFactory = Callable[[], Any]


def _default_reader_factory() -> Any:
    import easyocr

    return easyocr.Reader(["ar", "en"], gpu=False, verbose=False)


def make_easyocr_callable(
    *,
    reader_factory: ReaderFactory = _default_reader_factory,
) -> Callable[[bytes], str]:
    reader = reader_factory()

    def ocr(image_bytes: bytes) -> str:
        import numpy as np

        with Image.open(BytesIO(image_bytes)) as image:
            normalized = ImageOps.exif_transpose(image).convert("RGB")
            pixels = np.asarray(normalized)
        lines = reader.readtext(pixels, detail=0, paragraph=False)
        if not isinstance(lines, list):
            raise ValueError("EasyOCR readtext must return a list")
        return "\n".join(str(line) for line in lines)

    return ocr


def run_easyocr_numeric_benchmark(
    payload: dict[str, Any],
    source: dict[str, Any],
    *,
    reader_factory: ReaderFactory = _default_reader_factory,
) -> dict[str, object]:
    result = run_misraj_numeric_benchmark(
        payload,
        source,
        ocr_callable=make_easyocr_callable(reader_factory=reader_factory),
    )
    result["benchmark"] = "c29-misraj-easyocr-exact-numeric-safety"
    result["engine"] = "easyocr"
    result["engine_config"] = {
        "languages": ["ar", "en"],
        "gpu": False,
        "paragraph": False,
    }
    return result
