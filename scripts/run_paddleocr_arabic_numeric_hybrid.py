"""Benchmark a local dual-pass Arabic + numeric OCR strategy on synthetic fixtures."""

from __future__ import annotations

import argparse
import json
import platform
import re
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from paddleocr import PaddleOCR

DET_MODEL = "PP-OCRv6_small_det"
ARABIC_REC_MODEL = "arabic_PP-OCRv5_mobile_rec"
NUMERIC_REC_MODEL = "PP-OCRv6_small_rec"


def _font(size: int):
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _render(text: str, path: Path, *, rotate: float = 0.0, blur: float = 0.0) -> None:
    image = Image.new("RGB", (1500, 420), "white")
    draw = ImageDraw.Draw(image)
    draw.text((90, 120), text, fill="black", font=_font(104))
    if rotate:
        image = image.rotate(rotate, resample=Image.Resampling.BICUBIC, fillcolor="white")
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur))
    image.save(path)


def _extract(result: object) -> str:
    rows: list[str] = []
    for item in result:
        payload = item.json["res"]
        rows.extend(str(value) for value in payload.get("rec_texts", ()))
    return "\n".join(rows)


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text).lower().replace(",", ".")


def _case(arabic_ocr, numeric_ocr, *, case_id: str, text: str, arabic_tokens: tuple[str, ...], numeric_tokens: tuple[str, ...], output_dir: Path, rotate: float = 0.0, blur: float = 0.0) -> dict[str, object]:
    path = output_dir / f"{case_id}.png"
    _render(text, path, rotate=rotate, blur=blur)
    started = time.perf_counter()
    arabic_text = _extract(arabic_ocr.predict(str(path)))
    numeric_text = _extract(numeric_ocr.predict(str(path)))
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    ar_norm = _norm(arabic_text)
    num_norm = _norm(numeric_text)
    missing_arabic = tuple(token for token in arabic_tokens if _norm(token) not in ar_norm)
    missing_numeric = tuple(token for token in numeric_tokens if _norm(token) not in num_norm)
    return {
        "case_id": case_id,
        "fixture": path.name,
        "reference": text,
        "arabic_output": arabic_text,
        "numeric_output": numeric_text,
        "missing_arabic": missing_arabic,
        "missing_numeric": missing_numeric,
        "passed": not missing_arabic and not missing_numeric,
        "latency_ms_dual_pass": latency_ms,
    }


def run(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_started = time.perf_counter()
    common = dict(
        text_detection_model_name=DET_MODEL,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device="cpu",
    )
    arabic_ocr = PaddleOCR(text_recognition_model_name=ARABIC_REC_MODEL, **common)
    numeric_ocr = PaddleOCR(text_recognition_model_name=NUMERIC_REC_MODEL, **common)
    setup_ms = round((time.perf_counter() - setup_started) * 1000, 2)

    cases = (
        _case(arabic_ocr, numeric_ocr, case_id="arabic_glucose_54", text="سكر الدم 54", arabic_tokens=("سكر",), numeric_tokens=("54",), output_dir=output_dir),
        _case(arabic_ocr, numeric_ocr, case_id="arabic_glucose_rotated_68", text="سكر الدم 68", arabic_tokens=("سكر",), numeric_tokens=("68",), output_dir=output_dir, rotate=4.0),
        _case(arabic_ocr, numeric_ocr, case_id="arabic_hba1c_blur_74", text="السكر التراكمي 7.4", arabic_tokens=("السكر",), numeric_tokens=("7.4",), output_dir=output_dir, blur=1.2),
    )
    passed = sum(1 for case in cases if case["passed"])
    result = {
        "engine": "paddleocr-dual-pass",
        "benchmark": "c21-synthetic-arabic-numeric-hybrid",
        "pipeline_version": "3.7.0",
        "paddlepaddle_version": "3.2.2",
        "detection_model": DET_MODEL,
        "arabic_recognition_model": ARABIC_REC_MODEL,
        "numeric_recognition_model": NUMERIC_REC_MODEL,
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
    (output_dir / "paddleocr-arabic-numeric-hybrid.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
