"""Measure Arabic OCR robustness across controlled typography/rendering profiles.

Synthetic non-patient evidence only. The benchmark fails if any safety-critical
numeric token is lost, even when Arabic text is otherwise readable.
"""

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
REC_MODEL = "arabic_PP-OCRv5_mobile_rec"


def _font(profile: str, size: int):
    candidates = (
        (
            "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        )
        if profile == "rtl_naskh"
        else (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        )
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size), candidate
    raise RuntimeError(f"font unavailable for profile {profile}")


def _render(text: str, path: Path, *, profile: str, rotate: float = 0.0, blur: float = 0.0) -> str:
    image = Image.new("RGB", (1500, 420), "white")
    draw = ImageDraw.Draw(image)
    font, font_path = _font(profile, 104)
    if profile == "rtl_naskh":
        draw.text((1380, 100), text, fill="black", font=font, anchor="ra", direction="rtl", language="ar")
    elif profile == "generic_dejavu":
        draw.text((90, 120), text, fill="black", font=font)
    else:
        raise ValueError(f"unsupported profile: {profile}")
    if rotate:
        image = image.rotate(rotate, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white")
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur))
    image.save(path)
    return font_path


def _norm(value: str) -> str:
    return re.sub(r"[\s\u200f\u200e]+", "", value).lower().replace(",", ".")


def _extract(result: object) -> tuple[str, tuple[float, ...]]:
    rows: list[str] = []
    scores: list[float] = []
    for item in result:
        payload = item.json["res"]
        rows.extend(str(value) for value in payload.get("rec_texts", ()))
        scores.extend(float(value) for value in payload.get("rec_scores", ()))
    return "\n".join(rows), tuple(scores)


def _case(ocr: PaddleOCR, output_dir: Path, *, profile: str, case_id: str, text: str, arabic_token: str, numeric_token: str, rotate: float = 0.0, blur: float = 0.0) -> dict[str, object]:
    path = output_dir / f"{profile}_{case_id}.png"
    font_path = _render(text, path, profile=profile, rotate=rotate, blur=blur)
    started = time.perf_counter()
    extracted, scores = _extract(ocr.predict(str(path)))
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    normalized = _norm(extracted)
    arabic_ok = _norm(arabic_token) in normalized
    numeric_ok = _norm(numeric_token) in normalized
    return {
        "profile": profile,
        "case_id": case_id,
        "fixture": path.name,
        "font": font_path,
        "reference": text,
        "extracted": extracted,
        "arabic_token": arabic_token,
        "numeric_token": numeric_token,
        "arabic_ok": arabic_ok,
        "numeric_ok": numeric_ok,
        "passed": arabic_ok and numeric_ok,
        "latency_ms": latency_ms,
        "mean_recognition_confidence": round(sum(scores) / len(scores), 6) if scores else None,
    }


def run(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_started = time.perf_counter()
    ocr = PaddleOCR(
        text_detection_model_name=DET_MODEL,
        text_recognition_model_name=REC_MODEL,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device="cpu",
    )
    setup_ms = round((time.perf_counter() - setup_started) * 1000, 2)

    cases: list[dict[str, object]] = []
    for profile in ("rtl_naskh", "generic_dejavu"):
        cases.extend(
            (
                _case(ocr, output_dir, profile=profile, case_id="glucose_54", text="سكر الدم 54", arabic_token="سكر", numeric_token="54"),
                _case(ocr, output_dir, profile=profile, case_id="glucose_rotated_68", text="سكر الدم 68", arabic_token="سكر", numeric_token="68", rotate=3.0),
                _case(ocr, output_dir, profile=profile, case_id="hba1c_blur_74", text="السكر التراكمي 7.4", arabic_token="السكر", numeric_token="7.4", blur=1.2),
            )
        )

    passed = sum(1 for case in cases if case["passed"])
    numeric_passed = sum(1 for case in cases if case["numeric_ok"])
    result = {
        "engine": "paddleocr",
        "benchmark": "c22-synthetic-arabic-robustness-matrix",
        "pipeline_version": "3.7.0",
        "paddlepaddle_version": "3.2.2",
        "detection_model": DET_MODEL,
        "recognition_model": REC_MODEL,
        "device": "cpu",
        "python": platform.python_version(),
        "patient_data": False,
        "provider_api": False,
        "paid_inference": False,
        "synthetic_only": True,
        "setup_ms": setup_ms,
        "passed": passed,
        "total": len(cases),
        "numeric_passed": numeric_passed,
        "numeric_total": len(cases),
        "all_passed": passed == len(cases),
        "numeric_safety_floor_passed": numeric_passed == len(cases),
        "cases": cases,
    }
    (output_dir / "paddleocr-arabic-robustness-matrix.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
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
