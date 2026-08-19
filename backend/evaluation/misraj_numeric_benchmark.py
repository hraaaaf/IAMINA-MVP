"""Exact numeric-safety benchmark for a pinned Misraj-DocOCR viewer slice.

The benchmark deliberately emits no raw ground-truth or OCR text. Both the
source ground truth and every sampled image must be hash-pinned before OCR.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import http.client
import re
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from urllib.parse import urlsplit

from PIL import Image, ImageOps

from evaluation.misraj_dataset_preflight import summarize_misraj_viewer
from evaluation.tesseract_arabic_camera_benchmark import extract_numeric_tokens


class MisrajNumericBenchmarkError(ValueError):
    pass


ImageFetcher = Callable[[str], bytes]
OCRCallable = Callable[[bytes], str]
_DATA_URI_RE = re.compile(r"^data:image/[^;]+;base64,(.+)$", re.DOTALL)


def _https_get(url: str, *, allowed_hosts: set[str], timeout: int = 60) -> bytes:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in allowed_hosts
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
    ):
        raise MisrajNumericBenchmarkError("unexpected image source host")
    target = parsed.path or "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    connection = http.client.HTTPSConnection(parsed.hostname, timeout=timeout)
    try:
        connection.request("GET", target, headers={"User-Agent": "IAMINA-C27/1.0"})
        response = connection.getresponse()
        if response.status != 200:
            raise MisrajNumericBenchmarkError(
                f"image source returned HTTP {response.status}"
            )
        return response.read()
    finally:
        connection.close()


def load_viewer_image_bytes(
    image: object,
    *,
    allowed_hosts: set[str],
    image_fetcher: ImageFetcher | None = None,
) -> bytes:
    if not isinstance(image, dict):
        raise MisrajNumericBenchmarkError("viewer image field must be an object")
    src = image.get("src")
    if not isinstance(src, str) or not src:
        raise MisrajNumericBenchmarkError("viewer image src is missing")

    data_match = _DATA_URI_RE.match(src)
    if data_match:
        try:
            return base64.b64decode(data_match.group(1), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise MisrajNumericBenchmarkError("invalid image data URI") from exc

    parsed = urlsplit(src)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise MisrajNumericBenchmarkError("viewer image src host is not pinned")
    fetcher = image_fetcher or (
        lambda value: _https_get(value, allowed_hosts=allowed_hosts)
    )
    return fetcher(src)


def tesseract_ocr_image_bytes(
    image_bytes: bytes,
    *,
    tesseract_bin: str = "tesseract",
    psm: int = 6,
) -> str:
    import subprocess
    from io import BytesIO

    if psm < 0 or psm > 13:
        raise MisrajNumericBenchmarkError("Tesseract psm must be between 0 and 13")
    with TemporaryDirectory(prefix="iamina-c27-") as tmp:
        normalized_path = Path(tmp) / "normalized.png"
        with Image.open(BytesIO(image_bytes)) as image:
            normalized = ImageOps.exif_transpose(image).convert("RGB")
            normalized.save(normalized_path, format="PNG")
        result = subprocess.run(
            [
                tesseract_bin,
                str(normalized_path),
                "stdout",
                "-l",
                "ara",
                "--psm",
                str(psm),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()


def run_misraj_numeric_benchmark(
    payload: dict[str, Any],
    source: dict[str, Any],
    *,
    ocr_callable: OCRCallable = tesseract_ocr_image_bytes,
    image_fetcher: ImageFetcher | None = None,
) -> dict[str, object]:
    expected_fingerprint = source.get("expected_sample_fingerprint_sha256")
    allowed_hosts_value = source.get("allowed_image_src_hosts")
    expected_image_hashes = source.get("expected_image_sha256_by_uuid")
    if not isinstance(expected_fingerprint, str) or len(expected_fingerprint) != 64:
        raise MisrajNumericBenchmarkError("C27 requires a pinned C26 sample fingerprint")
    if not isinstance(allowed_hosts_value, list):
        raise MisrajNumericBenchmarkError("C27 requires pinned image source hosts")
    if not isinstance(expected_image_hashes, dict) or not expected_image_hashes:
        raise MisrajNumericBenchmarkError("C27 requires pinned image SHA-256 values")
    allowed_hosts = {str(host) for host in allowed_hosts_value if str(host)}

    preflight = summarize_misraj_viewer(
        payload,
        expected_total_rows=int(source["expected_total_rows"]),
        expected_features=list(source["expected_features"]),
        expected_first_uuid=str(source["expected_first_uuid"]),
        expected_sample_fingerprint=expected_fingerprint,
    )
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != preflight["sampled_rows"]:
        raise MisrajNumericBenchmarkError("viewer rows are missing")
    if len(expected_image_hashes) != len(rows):
        raise MisrajNumericBenchmarkError("pinned image hash count does not match sample")

    cases: list[dict[str, object]] = []
    for item in rows:
        row = item.get("row") if isinstance(item, dict) else None
        if not isinstance(row, dict):
            raise MisrajNumericBenchmarkError("viewer row is malformed")
        uuid = row.get("uuid")
        markdown = row.get("markdown")
        if not isinstance(uuid, str) or not isinstance(markdown, str):
            raise MisrajNumericBenchmarkError("viewer UUID or ground truth is missing")
        expected_numbers = extract_numeric_tokens(markdown)
        if not expected_numbers:
            raise MisrajNumericBenchmarkError(f"fixture {uuid} has no numeric safety token")

        expected_image_hash = expected_image_hashes.get(uuid)
        if not isinstance(expected_image_hash, str) or len(expected_image_hash) != 64:
            raise MisrajNumericBenchmarkError(f"fixture {uuid} has no pinned image SHA-256")
        image_bytes = load_viewer_image_bytes(
            row.get("image"),
            allowed_hosts=allowed_hosts,
            image_fetcher=image_fetcher,
        )
        image_sha256 = hashlib.sha256(image_bytes).hexdigest()
        if image_sha256 != expected_image_hash:
            raise MisrajNumericBenchmarkError(f"fixture {uuid} image SHA-256 drifted")

        extracted = ocr_callable(image_bytes)
        extracted_numbers = extract_numeric_tokens(extracted)
        cases.append(
            {
                "uuid": uuid,
                "image_sha256": image_sha256,
                "expected_numeric_tokens": expected_numbers,
                "extracted_numeric_tokens": extracted_numbers,
                "numeric_ok": extracted_numbers == expected_numbers,
            }
        )

    safe_cases = sum(1 for case in cases if case["numeric_ok"])
    return {
        "benchmark": "c27-misraj-arabic-document-exact-numeric-safety",
        "engine": "tesseract",
        "language": "ara",
        "sample_fingerprint_sha256": expected_fingerprint,
        "source_images_pinned": True,
        "sampled_rows": len(cases),
        "numeric_safe_cases": safe_cases,
        "numeric_total": len(cases),
        "numeric_safety_floor_passed": safe_cases == len(cases),
        "raw_ground_truth_emitted": False,
        "raw_ocr_text_emitted": False,
        "real_camera_claim": False,
        "iamina_patient_data": False,
        "provider_api": False,
        "paid_inference": False,
        "cases": cases,
    }
