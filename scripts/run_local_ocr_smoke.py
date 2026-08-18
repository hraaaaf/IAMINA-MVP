"""Run a zero-egress synthetic OCR smoke benchmark.

This benchmark is deliberately small. It answers one question only: can the
existing local Tesseract path reliably read simple synthetic diabetes-relevant
Latin text/digits before IAMINA adds another OCR dependency?

No patient data, network model call, or cloud provider is involved.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

import pytesseract
from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def _render(lines: tuple[str, ...], path: Path) -> None:
    image = Image.new("L", (1400, 700), 255)
    draw = ImageDraw.Draw(image)
    font = _font(92)
    y = 90
    for line in lines:
        draw.text((90, y), line, fill=0, font=font)
        y += 180
    image.save(path)


def _run_case(case_id: str, lines: tuple[str, ...], required: tuple[str, ...], root: Path) -> dict:
    image_path = root / f"{case_id}.png"
    _render(lines, image_path)
    extracted = pytesseract.image_to_string(Image.open(image_path), config="--psm 6")
    normalized = _normalize(extracted)
    required_normalized = tuple(_normalize(token) for token in required)
    missing = tuple(token for token in required_normalized if token not in normalized)
    return {
        "case_id": case_id,
        "required": required,
        "extracted": extracted.strip(),
        "missing": missing,
        "passed": not missing,
    }


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="iamina-ocr-smoke-") as tmp:
        root = Path(tmp)
        cases = (
            _run_case(
                "synthetic_glucometer_54",
                ("54 mg/dL",),
                ("54", "mg/dL"),
                root,
            ),
            _run_case(
                "synthetic_lab_glucose_hba1c",
                ("GLUCOSE 108 mg/dL", "HbA1c 6.7 %"),
                ("GLUCOSE", "108", "HbA1c", "6.7"),
                root,
            ),
        )
    passed = sum(1 for case in cases if case["passed"])
    return {
        "engine": "tesseract",
        "engine_version": str(pytesseract.get_tesseract_version()).splitlines()[0],
        "scope": "synthetic Latin text/digits smoke baseline only",
        "patient_data": False,
        "network_provider": False,
        "passed": passed,
        "total": len(cases),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] == result["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
