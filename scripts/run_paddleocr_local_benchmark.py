"""Measure local PP-OCRv6 on synthetic diabetes-relevant OCR fixtures.

This benchmark performs local inference only. Paddle model weights may be downloaded
from the configured official model source during setup, but no patient data,
provider API, credentials, or paid inference call is used.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from paddleocr import PaddleOCR

MODEL_DET = "PP-OCRv6_small_det"
MODEL_REC = "PP-OCRv6_small_rec"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _render(lines: tuple[str, ...], path: Path) -> None:
    image = Image.new("RGB", (1500, 760), "white")
    draw = ImageDraw.Draw(image)
    font = _font(96)
    y = 90
    for line in lines:
        draw.text((90, y), line, fill="black", font=font)
        y += 210
    image.save(path)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def _extract_text(result: object) -> tuple[str, tuple[float, ...]]:
    rows: list[str] = []
    scores: list[float] = []
    for item in result:  # PaddleOCR returns a list-like result collection.
        payload = item.json["res"]
        rows.extend(str(value) for value in payload.get("rec_texts", ()))
        scores.extend(float(value) for value in payload.get("rec_scores", ()))
    return "\n".join(rows), tuple(scores)


def _contains_all(text: str, required: tuple[str, ...]) -> tuple[bool, tuple[str, ...]]:
    normalized = _normalize(text)
    missing = tuple(token for token in required if _normalize(token) not in normalized)
    return not missing, missing


def _run_case(
    ocr: PaddleOCR,
    *,
    case_id: str,
    lines: tuple[str, ...],
    required: tuple[str, ...],
    output_dir: Path,
) -> dict[str, object]:
    image_path = output_dir / f"{case_id}.png"
    _render(lines, image_path)

    started = time.perf_counter()
    result = ocr.predict(str(image_path))
    latency_ms = round((time.perf_counter() - started) * 1000, 2)

    extracted, scores = _extract_text(result)
    passed, missing = _contains_all(extracted, required)
    return {
        "case_id": case_id,
        "fixture": image_path.name,
        "required": required,
        "extracted": extracted,
        "missing": missing,
        "passed": passed,
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
            case_id="synthetic_glucometer_54",
            lines=("54 mg/dL",),
            required=("54", "mg/dL"),
            output_dir=output_dir,
        ),
        _run_case(
            ocr,
            case_id="synthetic_lab_hba1c_glucose",
            lines=("HbA1c 7.4 %", "Glycemie a jeun 1.32 g/L"),
            required=("HbA1c", "7.4", "1.32", "g/L"),
            output_dir=output_dir,
        ),
    )

    passed = sum(1 for case in cases if case["passed"])
    result: dict[str, object] = {
        "engine": "paddleocr",
        "pipeline_version": "3.7.0",
        "paddlepaddle_version": "3.2.2",
        "detection_model": MODEL_DET,
        "recognition_model": MODEL_REC,
        "device": "cpu",
        "python": platform.python_version(),
        "patient_data": False,
        "provider_api": False,
        "paid_inference": False,
        "model_weight_download_allowed": True,
        "setup_ms": setup_ms,
        "passed": passed,
        "total": len(cases),
        "all_passed": passed == len(cases),
        "cases": cases,
    }
    (output_dir / "paddleocr-local-benchmark.json").write_text(
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
