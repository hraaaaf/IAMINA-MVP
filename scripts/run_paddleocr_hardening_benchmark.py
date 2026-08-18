"""Stress PP-OCRv6 with harder synthetic diabetes-relevant OCR fixtures."""

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
MODEL_REC = "PP-OCRv6_small_rec"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _base(lines: tuple[str, ...], *, fg: int = 0, bg: int = 255) -> Image.Image:
    image = Image.new("L", (1500, 760), bg)
    draw = ImageDraw.Draw(image)
    font = _font(96)
    y = 90
    for line in lines:
        draw.text((90, y), line, fill=fg, font=font)
        y += 210
    return image.convert("RGB")


def _fixture(kind: str, lines: tuple[str, ...], path: Path) -> None:
    if kind == "rotate":
        image = _base(lines).rotate(4.0, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white")
        image.save(path)
        return
    if kind == "low_contrast":
        image = _base(lines, fg=105, bg=225)
        image.save(path)
        return
    if kind == "blur_jpeg":
        image = _base(lines).filter(ImageFilter.GaussianBlur(radius=1.6))
        image.save(path.with_suffix(".jpg"), quality=55)
        return
    raise ValueError(f"unsupported fixture transform: {kind}")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def _extract(result: object) -> tuple[str, tuple[float, ...]]:
    rows: list[str] = []
    scores: list[float] = []
    for item in result:
        payload = item.json["res"]
        rows.extend(str(value) for value in payload.get("rec_texts", ()))
        scores.extend(float(value) for value in payload.get("rec_scores", ()))
    return "\n".join(rows), tuple(scores)


def _run_case(
    ocr: PaddleOCR,
    *,
    case_id: str,
    kind: str,
    lines: tuple[str, ...],
    required: tuple[str, ...],
    output_dir: Path,
) -> dict[str, object]:
    suffix = ".jpg" if kind == "blur_jpeg" else ".png"
    path = output_dir / f"{case_id}{suffix}"
    _fixture(kind, lines, path)
    started = time.perf_counter()
    result = ocr.predict(str(path))
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    extracted, scores = _extract(result)
    normalized = _normalize(extracted)
    missing = tuple(token for token in required if _normalize(token) not in normalized)
    return {
        "case_id": case_id,
        "transform": kind,
        "fixture": path.name,
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
        _run_case(
            ocr,
            case_id="glucometer_rotated_54",
            kind="rotate",
            lines=("54 mg/dL",),
            required=("54", "mg/dL"),
            output_dir=output_dir,
        ),
        _run_case(
            ocr,
            case_id="glucometer_low_contrast_68",
            kind="low_contrast",
            lines=("68 mg/dL",),
            required=("68", "mg/dL"),
            output_dir=output_dir,
        ),
        _run_case(
            ocr,
            case_id="lab_blur_jpeg",
            kind="blur_jpeg",
            lines=("HbA1c 7.4 %", "Glycemie a jeun 1.32 g/L"),
            required=("HbA1c", "7.4", "1.32", "g/L"),
            output_dir=output_dir,
        ),
    )
    passed = sum(1 for case in cases if case["passed"])
    result: dict[str, object] = {
        "engine": "paddleocr",
        "benchmark": "c15-synthetic-hardening",
        "pipeline_version": "3.7.0",
        "paddlepaddle_version": "3.2.2",
        "detection_model": MODEL_DET,
        "recognition_model": MODEL_REC,
        "device": "cpu",
        "python": platform.python_version(),
        "patient_data": False,
        "provider_api": False,
        "paid_inference": False,
        "setup_ms": setup_ms,
        "passed": passed,
        "total": len(cases),
        "all_passed": passed == len(cases),
        "cases": cases,
    }
    (output_dir / "paddleocr-hardening-benchmark.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
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
