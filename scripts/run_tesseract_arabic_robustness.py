"""Benchmark Tesseract Arabic on the same C22 synthetic safety matrix."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _font(profile: str, size: int):
    candidates = {
        "rtl_naskh": [
            "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
            "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf",
        ],
        "generic_dejavu": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    }[profile]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size), candidate
    raise RuntimeError(f"font unavailable for {profile}")


def _render(profile: str, text: str, path: Path, *, rotate: float = 0.0, blur: float = 0.0) -> str:
    font, font_path = _font(profile, 104)
    image = Image.new("RGB", (1500, 420), "white")
    draw = ImageDraw.Draw(image)
    if profile == "rtl_naskh":
        draw.text((1380, 100), text, fill="black", font=font, anchor="ra", direction="rtl", language="ar")
    else:
        draw.text((90, 120), text, fill="black", font=font)
    if rotate:
        image = image.rotate(rotate, resample=Image.Resampling.BICUBIC, fillcolor="white")
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur))
    image.save(path)
    return font_path


def _norm(value: str) -> str:
    return re.sub(r"[\s\u200f\u200e]+", "", value).lower().replace(",", ".")


def _ocr(path: Path) -> str:
    result = subprocess.run(
        ["tesseract", str(path), "stdout", "-l", "ara", "--psm", "6"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _case(profile: str, case_id: str, text: str, arabic_token: str, numeric_token: str, output_dir: Path, *, rotate: float = 0.0, blur: float = 0.0):
    path = output_dir / f"{profile}_{case_id}.png"
    font = _render(profile, text, path, rotate=rotate, blur=blur)
    started = time.perf_counter()
    extracted = _ocr(path)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    normalized = _norm(extracted)
    arabic_ok = _norm(arabic_token) in normalized
    numeric_ok = _norm(numeric_token) in normalized
    return {
        "profile": profile,
        "case_id": case_id,
        "fixture": path.name,
        "font": font,
        "reference": text,
        "extracted": extracted,
        "arabic_token": arabic_token,
        "numeric_token": numeric_token,
        "arabic_ok": arabic_ok,
        "numeric_ok": numeric_ok,
        "passed": arabic_ok and numeric_ok,
        "latency_ms": latency_ms,
    }


def run(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    for profile in ("rtl_naskh", "generic_dejavu"):
        cases.extend([
            _case(profile, "glucose_54", "سكر الدم 54", "سكر", "54", output_dir),
            _case(profile, "glucose_rotated_68", "سكر الدم 68", "سكر", "68", output_dir, rotate=3.0),
            _case(profile, "hba1c_blur_74", "السكر التراكمي 7.4", "السكر", "7.4", output_dir, blur=1.2),
        ])
    passed = sum(1 for case in cases if case["passed"])
    numeric_passed = sum(1 for case in cases if case["numeric_ok"])
    version = subprocess.run(["tesseract", "--version"], check=True, capture_output=True, text=True).stdout.splitlines()[0]
    result = {
        "engine": "tesseract",
        "benchmark": "c23-synthetic-arabic-robustness-matrix",
        "engine_version": version,
        "language": "ara",
        "patient_data": False,
        "provider_api": False,
        "paid_inference": False,
        "synthetic_only": True,
        "passed": passed,
        "total": len(cases),
        "numeric_passed": numeric_passed,
        "numeric_total": len(cases),
        "all_passed": passed == len(cases),
        "numeric_safety_floor_passed": numeric_passed == len(cases),
        "cases": cases,
    }
    (output_dir / "tesseract-arabic-robustness.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["all_passed"] and result["numeric_safety_floor_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
