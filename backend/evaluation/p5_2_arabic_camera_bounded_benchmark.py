"""P5-2 bounded Arabic real-camera OCR evidence on public receipt photos.

Source: IslamMesabah/AraReceipt (MIT), derived from ReceiptSense. The run resolves
and records the exact Hugging Face dataset revision, then selects the first
eligible annotations in dataset order. No image or raw transcription is retained
in the evidence artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

DATASET_ID = "IslamMesabah/AraReceipt"
DATASET_LICENSE = "MIT"
DATASET_CARD = "https://huggingface.co/datasets/IslamMesabah/AraReceipt"
ARABIC_CASES = 6
NUMERIC_CASES = 6
TESSERACT_LANG = "ara"
TESSERACT_CONFIG = "--psm 7"

_ARABIC = re.compile(r"[\u0600-\u06ff]")
_ARABIC_MARKS = re.compile(r"[\u0640\u064b-\u065f\u0670\u06d6-\u06ed]")
_NUMBER = re.compile(r"\d+(?:[.,٫]\d+)?")
_DIGIT_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


class EvidenceConfigurationError(RuntimeError):
    """Raised when the public evidence source cannot satisfy the frozen contract."""


@dataclass(frozen=True, slots=True)
class SelectedAnnotation:
    row_id: int
    annotation_index: int
    kind: str
    text: str
    box: tuple[int, ...]


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).translate(_DIGIT_TRANSLATION)
    normalized = _ARABIC_MARKS.sub("", normalized)
    return "".join(ch.casefold() for ch in normalized if ch.isalnum())


def numeric_tokens(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", value).translate(_DIGIT_TRANSLATION)
    return tuple(token.replace("٫", ".").replace(",", ".") for token in _NUMBER.findall(normalized))


def select_annotations(rows: Iterable[dict[str, Any]]) -> tuple[SelectedAnnotation, ...]:
    arabic: list[SelectedAnnotation] = []
    numeric: list[SelectedAnnotation] = []
    for row in sorted(rows, key=lambda item: int(item["id"])):
        for index, annotation in enumerate(row["annotations"]):
            text = str(annotation.get("text") or "").strip()
            box = tuple(int(value) for value in annotation.get("box") or ())
            if len(box) != 8 or not text:
                continue
            numbers = numeric_tokens(text)
            if len(arabic) < ARABIC_CASES and _ARABIC.search(text) and not numbers:
                arabic.append(SelectedAnnotation(int(row["id"]), index, "arabic_text", text, box))
            if len(numeric) < NUMERIC_CASES and numbers:
                numeric.append(SelectedAnnotation(int(row["id"]), index, "numeric", text, box))
            if len(arabic) == ARABIC_CASES and len(numeric) == NUMERIC_CASES:
                return tuple(arabic + numeric)
    raise EvidenceConfigurationError(
        f"dataset did not yield {ARABIC_CASES} Arabic and {NUMERIC_CASES} numeric bounded cases"
    )


def _crop(image, box: tuple[int, ...]):
    xs = box[0::2]
    ys = box[1::2]
    left, right = max(0, min(xs)), min(image.width, max(xs))
    top, bottom = max(0, min(ys)), min(image.height, max(ys))
    if right <= left or bottom <= top:
        raise EvidenceConfigurationError("invalid annotation crop")
    pad_x = max(4, int((right - left) * 0.05))
    pad_y = max(4, int((bottom - top) * 0.10))
    return image.crop((max(0, left - pad_x), max(0, top - pad_y), min(image.width, right + pad_x), min(image.height, bottom + pad_y)))


def _image_hash(image) -> str:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def _text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    from datasets import load_dataset
    from huggingface_hub import HfApi
    import pytesseract

    info = HfApi().dataset_info(DATASET_ID)
    revision = str(info.sha or "").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise EvidenceConfigurationError("dataset revision SHA unavailable")
    dataset = load_dataset(DATASET_ID, split="train", revision=revision)
    rows = [dataset[index] for index in range(len(dataset))]
    selected = select_annotations(rows)
    row_by_id = {int(row["id"]): row for row in rows}

    results: list[dict[str, Any]] = []
    arabic_exact = 0
    numeric_exact = 0
    for case in selected:
        row = row_by_id[case.row_id]
        crop = _crop(row["image"], case.box)
        observed = pytesseract.image_to_string(crop, lang=TESSERACT_LANG, config=TESSERACT_CONFIG).strip()
        if case.kind == "numeric":
            expected_tokens = numeric_tokens(case.text)
            observed_tokens = numeric_tokens(observed)
            exact = expected_tokens == observed_tokens
            numeric_exact += int(exact)
            expected_fingerprint = _text_hash("|".join(expected_tokens))
            observed_fingerprint = _text_hash("|".join(observed_tokens))
        else:
            expected_normalized = normalize_text(case.text)
            observed_normalized = normalize_text(observed)
            exact = expected_normalized == observed_normalized
            arabic_exact += int(exact)
            expected_fingerprint = _text_hash(expected_normalized)
            observed_fingerprint = _text_hash(observed_normalized)
        results.append({
            "row_id": case.row_id,
            "annotation_index": case.annotation_index,
            "kind": case.kind,
            "crop_sha256": _image_hash(crop),
            "expected_sha256": expected_fingerprint,
            "observed_sha256": observed_fingerprint,
            "exact": exact,
            "raw_text_retained": False,
        })

    passed = arabic_exact == ARABIC_CASES and numeric_exact == NUMERIC_CASES
    report = {
        "run_date": today.isoformat(),
        "dataset": {
            "id": DATASET_ID,
            "revision": revision,
            "license": DATASET_LICENSE,
            "card": DATASET_CARD,
            "real_camera_source": True,
            "patient_data": False,
            "source_privacy_note": "ReceiptSense reports consented collection and a four-step PII redaction process; AraReceipt exposes reviewed annotations derived from it.",
        },
        "engine": {"name": "tesseract", "language": TESSERACT_LANG, "config": TESSERACT_CONFIG},
        "selection": {
            "policy": "first eligible annotations in ascending dataset row id and annotation order",
            "arabic_cases": ARABIC_CASES,
            "numeric_cases": NUMERIC_CASES,
            "post_result_case_selection": False,
        },
        "hard_floor": {
            "arabic_normalized_exact_required": f"{ARABIC_CASES}/{ARABIC_CASES}",
            "numeric_sequence_exact_required": f"{NUMERIC_CASES}/{NUMERIC_CASES}",
        },
        "scores": {
            "arabic_normalized_exact": arabic_exact,
            "arabic_total": ARABIC_CASES,
            "numeric_sequence_exact": numeric_exact,
            "numeric_total": NUMERIC_CASES,
        },
        "verdict": "PASS" if passed else "FAIL",
        "proof_boundaries": {
            "bounded_fields_only": True,
            "full_document_primary_qualified": False,
            "production_or_patient_traffic": False,
            "raw_source_text_or_images_in_artifact": False,
        },
        "cases": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_benchmark(output_path=args.output, today=date.today())
    print(json.dumps({"verdict": report["verdict"], "revision": report["dataset"]["revision"], "scores": report["scores"]}, ensure_ascii=False))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
