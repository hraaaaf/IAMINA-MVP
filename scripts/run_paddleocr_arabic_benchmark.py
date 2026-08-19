"""Measure local Arabic OCR on controlled synthetic diabetes-relevant fixtures."""

from __future__ import annotations

import argparse
import json
import platform
import re
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from paddleocr import PaddleOCR

MODEL_DET = "PP-OCRv6_small_det"
MODEL_REC = "arabic_PP-OCRv5_mobile_rec"


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = (
        "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    raise RuntimeError("Arabic-capable benchmark font is unavailable")


def _render(text: str, path: Path, *, rotate: float = 0.0, blur: float = 0.0) -> None:
    image = Image.new("RGB", (1500, 420), "white")
    draw = ImageDraw.Draw(image)
    font = _font(104)
    draw.text((1380, 100), text, fill="black", font=font, anchor="ra", direction="rtl", language="ar")
    if rotate:
        image = image.rotate(rotate, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white")
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur))
    image.save(path)


def _normalize(value: str) -> str:
    return re.sub(r"[\s\u200f\u200e]+", "", value).lower()


def _extract(result: object) -> tuple[str, tuple[float, ...]]:
    rows: list[str] = []
    scores: list[float] = []
    for item in result:
        payload = item.json["res"]
        rows.extend(str(value) for value in payload.get("rec_texts", ()))
        scores.extend(float(value) for value in payload.get("rec_scores", ()))
    return "\n".join(rows), tuple(scores)


def _case(ocr: PaddleOCR, output_dir: Path, case_id: str, text: str, required: tuple[str, ...], *, rotate: float = 0.0, blur: float = 0.0) -> dict[str, object]:
    path = output_dir / f"{case_id}.png"
    _render(text, path, rotate=rotate, blur=blur)
    started = time.perf_counter()
    extracted, scores = _extract(ocr.predict(str(path)))
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    normalized = _normalize(extracted)
    missing = tuple(token for token in required if _normalize(token) not in normalized)
    return {
        "case_id": case_id,
        "fixture": path.name,
        "reference": text,
        "required": required,
        "extracted": extracted,
        "missing": missing,
        "passed": not missing,
        "latency_ms": latency_ms,
        "mean_recognition_confidence": round(sum(scores) / len(scores), 6) if scores else None,
    }


def run(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_started = time.perf_counter()
    ocr = PaddleOCR(
        text_detection_model_name=MODEL_DET,
        text_recognition_model_name=MODEL_REC,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device="cpu",
    )
    setup_ms = round((time.perf_counter() - setup_started) * 1000, 2)
    cases = (
        _case(ocr, output_dir, "arabic_glucose_54", "سكر الدم 54", ("سكر", "54")),
        _case(ocr, output_dir, "arabic_glucose_rotated_68", "سكر الدم 68", ("سكر", "68"), rotate=3.0),
        _case(ocr, output_dir, "arabic_hba1c_blur_74", "السكر التراكمي 7.4", ("السكر", "7.4"), blur=1.2),
    )
    passed = sum(1 for case in cases if case["passed"])
    result: dict[str, object] = {
        "engine": "paddleocr",
        "benchmark": "c20-synthetic-arabic",
        "pipeline_version": "3.7.0",
        "paddlepaddle_version": "3.2.2",
        "detection_model": MODEL_DET,
        "recognition_model": MODEL_REC,
        "device": "cpu",
        "python": platform.python_version(),
        "patient_data": False,
        "provider_api": False,
        "paid_inference": False,
        "synthetic_only": True,
        "setup_ms": setup_ms,
        "passed": passed,
        "total": len(cases),
        "all_passed": passed == len(cases),
        "cases": cases,
    }
    (output_dir / "paddleocr-arabic-benchmark.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
