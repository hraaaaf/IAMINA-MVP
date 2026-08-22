"""FRUG-1 exact-numeric safety + wasteful-ingest reduction benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image

from evaluation.misraj_dataset_preflight import summarize_misraj_viewer
from evaluation.misraj_numeric_benchmark import (
    MisrajNumericBenchmarkError,
    load_viewer_image_bytes,
    tesseract_ocr_image_bytes,
)
from evaluation.tesseract_arabic_camera_benchmark import extract_numeric_tokens


class Frug1IngestBenchmarkError(ValueError):
    pass


_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}

_REDUCTION_FIXTURE_KIND = "jpeg-q100-444-from-pinned-source-raster"


def _image_kind(image_bytes: bytes) -> tuple[str, str]:
    with Image.open(BytesIO(image_bytes)) as image:
        value = _FORMATS.get(str(image.format).upper())
    if value is None:
        return "application/octet-stream", ".bin"
    return value


def _high_quality_jpeg_fixture(image_bytes: bytes) -> bytes:
    """Create a deterministic camera-like, byte-heavy JPEG from a pinned raster."""
    with Image.open(BytesIO(image_bytes)) as image:
        raster = image.convert("RGB")
        output = BytesIO()
        raster.save(
            output,
            format="JPEG",
            quality=100,
            subsampling=0,
            optimize=False,
        )
    return output.getvalue()


def _run_production_minimizer(
    image_bytes: bytes,
    *,
    filename: str,
    mime_type: str,
    frontend_dir: Path,
) -> tuple[bytes, dict[str, object]]:
    with TemporaryDirectory(prefix="iamina-frug1-") as tmp:
        tmp_path = Path(tmp)
        input_path = tmp_path / filename
        output_path = tmp_path / "upload.bin"
        metrics_path = tmp_path / "metrics.json"
        input_path.write_bytes(image_bytes)
        subprocess.run(
            [
                "dart",
                "run",
                "tool/frug1_minimize_image.dart",
                str(input_path),
                str(output_path),
                filename,
                mime_type,
                str(metrics_path),
            ],
            cwd=frontend_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        if not metrics_path.is_file():
            raise Frug1IngestBenchmarkError("Dart minimizer emitted no metrics file")
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise Frug1IngestBenchmarkError("Dart minimizer metrics file is invalid") from exc
        if not isinstance(metrics, dict):
            raise Frug1IngestBenchmarkError("Dart minimizer metrics file is malformed")
        return output_path.read_bytes(), metrics


def _numeric_tokens_after(
    upload_bytes: bytes,
    *,
    source_bytes: bytes,
    source_numbers: list[str],
) -> list[str]:
    if upload_bytes == source_bytes:
        return source_numbers
    return extract_numeric_tokens(tesseract_ocr_image_bytes(upload_bytes))


def run_frug1_ingest_benchmark(
    payload: dict[str, Any],
    source: dict[str, Any],
    *,
    frontend_dir: Path,
) -> dict[str, object]:
    expected_fingerprint = source.get("expected_sample_fingerprint_sha256")
    expected_image_hashes = source.get("expected_image_sha256_by_uuid")
    allowed_hosts_value = source.get("allowed_image_src_hosts")
    if not isinstance(expected_fingerprint, str) or len(expected_fingerprint) != 64:
        raise Frug1IngestBenchmarkError("FRUG-1 requires pinned sample fingerprint")
    if not isinstance(expected_image_hashes, dict) or not expected_image_hashes:
        raise Frug1IngestBenchmarkError("FRUG-1 requires pinned source image hashes")
    if not isinstance(allowed_hosts_value, list):
        raise Frug1IngestBenchmarkError("FRUG-1 requires pinned image hosts")
    allowed_hosts = {str(value) for value in allowed_hosts_value if str(value)}

    preflight = summarize_misraj_viewer(
        payload,
        expected_total_rows=int(source["expected_total_rows"]),
        expected_features=list(source["expected_features"]),
        expected_first_uuid=str(source["expected_first_uuid"]),
        expected_sample_fingerprint=expected_fingerprint,
    )
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != preflight["sampled_rows"]:
        raise Frug1IngestBenchmarkError("viewer rows are missing")

    cases: list[dict[str, object]] = []
    reduction_cases: list[dict[str, object]] = []
    source_sizes: list[int] = []
    upload_sizes: list[int] = []
    reduction_source_sizes: list[int] = []
    reduction_upload_sizes: list[int] = []

    for item in rows:
        row = item.get("row") if isinstance(item, dict) else None
        if not isinstance(row, dict):
            raise Frug1IngestBenchmarkError("viewer row is malformed")
        uuid = row.get("uuid")
        markdown = row.get("markdown")
        if not isinstance(uuid, str) or not isinstance(markdown, str):
            raise Frug1IngestBenchmarkError("viewer UUID or ground truth is missing")
        expected_numbers = extract_numeric_tokens(markdown)
        if not expected_numbers:
            raise Frug1IngestBenchmarkError(f"fixture {uuid} has no numeric token")

        image_bytes = load_viewer_image_bytes(
            row.get("image"),
            allowed_hosts=allowed_hosts,
        )
        source_hash = hashlib.sha256(image_bytes).hexdigest()
        if source_hash != expected_image_hashes.get(uuid):
            raise MisrajNumericBenchmarkError(f"fixture {uuid} image SHA-256 drifted")

        baseline_numbers = extract_numeric_tokens(tesseract_ocr_image_bytes(image_bytes))
        mime_type, suffix = _image_kind(image_bytes)
        upload_bytes, metrics = _run_production_minimizer(
            image_bytes,
            filename=f"{uuid}{suffix}",
            mime_type=mime_type,
            frontend_dir=frontend_dir,
        )
        minimized_numbers = _numeric_tokens_after(
            upload_bytes,
            source_bytes=image_bytes,
            source_numbers=baseline_numbers,
        )
        baseline_ok = baseline_numbers == expected_numbers
        minimized_ok = minimized_numbers == expected_numbers
        numeric_preserved = minimized_numbers == baseline_numbers
        regression = not numeric_preserved
        source_sizes.append(len(image_bytes))
        upload_sizes.append(len(upload_bytes))
        cases.append(
            {
                "uuid": uuid,
                "source_image_sha256": source_hash,
                "upload_sha256": hashlib.sha256(upload_bytes).hexdigest(),
                "source_bytes": len(image_bytes),
                "upload_bytes": len(upload_bytes),
                "transformed": bool(metrics.get("transformed")),
                "baseline_numeric_ok": baseline_ok,
                "minimized_numeric_ok": minimized_ok,
                "numeric_preserved": numeric_preserved,
                "numeric_regression": regression,
            }
        )

        reduction_source = _high_quality_jpeg_fixture(image_bytes)
        reduction_source_numbers = extract_numeric_tokens(
            tesseract_ocr_image_bytes(reduction_source)
        )
        reduction_upload, reduction_metrics = _run_production_minimizer(
            reduction_source,
            filename=f"{uuid}-camera.jpg",
            mime_type="image/jpeg",
            frontend_dir=frontend_dir,
        )
        reduction_minimized_numbers = _numeric_tokens_after(
            reduction_upload,
            source_bytes=reduction_source,
            source_numbers=reduction_source_numbers,
        )
        reduction_numeric_preserved = (
            reduction_minimized_numbers == reduction_source_numbers
        )
        reduction_source_sizes.append(len(reduction_source))
        reduction_upload_sizes.append(len(reduction_upload))
        reduction_cases.append(
            {
                "uuid": uuid,
                "fixture_kind": _REDUCTION_FIXTURE_KIND,
                "fixture_sha256": hashlib.sha256(reduction_source).hexdigest(),
                "upload_sha256": hashlib.sha256(reduction_upload).hexdigest(),
                "source_bytes": len(reduction_source),
                "upload_bytes": len(reduction_upload),
                "transformed": bool(reduction_metrics.get("transformed")),
                "numeric_preserved": reduction_numeric_preserved,
                "numeric_regression": not reduction_numeric_preserved,
            }
        )

    baseline_safe = sum(1 for case in cases if case["baseline_numeric_ok"])
    minimized_safe = sum(1 for case in cases if case["minimized_numeric_ok"])
    preserved_cases = sum(1 for case in cases if case["numeric_preserved"])
    regressions = sum(1 for case in cases if case["numeric_regression"])
    transformed_cases = sum(1 for case in cases if case["transformed"])
    median_source = float(statistics.median(source_sizes))
    median_upload = float(statistics.median(upload_sizes))
    total_source = sum(source_sizes)
    total_upload = sum(upload_sizes)

    reduction_preserved = sum(
        1 for case in reduction_cases if case["numeric_preserved"]
    )
    reduction_regressions = sum(
        1 for case in reduction_cases if case["numeric_regression"]
    )
    reduction_transformed = sum(1 for case in reduction_cases if case["transformed"])
    reduction_median_source = float(statistics.median(reduction_source_sizes))
    reduction_median_upload = float(statistics.median(reduction_upload_sizes))
    reduction_total_source = sum(reduction_source_sizes)
    reduction_total_upload = sum(reduction_upload_sizes)

    passed = (
        regressions == 0
        and preserved_cases == len(cases)
        and minimized_safe >= baseline_safe
        and reduction_regressions == 0
        and reduction_preserved == len(reduction_cases)
        and reduction_transformed == len(reduction_cases)
        and reduction_median_upload < reduction_median_source
        and reduction_total_upload < reduction_total_source
    )

    return {
        "benchmark": "frug1-ingest-minimization-exact-numeric",
        "dataset": str(source.get("dataset")),
        "sample_fingerprint_sha256": expected_fingerprint,
        "source_images_pinned": True,
        "sampled_rows": len(cases),
        "baseline_numeric_safe_cases": baseline_safe,
        "minimized_numeric_safe_cases": minimized_safe,
        "numeric_total": len(cases),
        "numeric_preserved_cases": preserved_cases,
        "numeric_regressions": regressions,
        "transformed_cases": transformed_cases,
        "median_source_bytes": median_source,
        "median_upload_bytes": median_upload,
        "median_reduction_fraction": 1.0 - (median_upload / median_source),
        "total_source_bytes": total_source,
        "total_upload_bytes": total_upload,
        "total_reduction_fraction": 1.0 - (total_upload / total_source),
        "reduction_fixture_kind": _REDUCTION_FIXTURE_KIND,
        "reduction_fixture_total": len(reduction_cases),
        "reduction_fixture_numeric_preserved_cases": reduction_preserved,
        "reduction_fixture_numeric_regressions": reduction_regressions,
        "reduction_fixture_transformed_cases": reduction_transformed,
        "reduction_fixture_median_source_bytes": reduction_median_source,
        "reduction_fixture_median_upload_bytes": reduction_median_upload,
        "reduction_fixture_median_reduction_fraction": 1.0
        - (reduction_median_upload / reduction_median_source),
        "reduction_fixture_total_source_bytes": reduction_total_source,
        "reduction_fixture_total_upload_bytes": reduction_total_upload,
        "reduction_fixture_total_reduction_fraction": 1.0
        - (reduction_total_upload / reduction_total_source),
        "passed": passed,
        "raw_ground_truth_emitted": False,
        "raw_ocr_text_emitted": False,
        "iamina_patient_data": False,
        "provider_api": False,
        "paid_inference": False,
        "cases": cases,
        "reduction_cases": reduction_cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("viewer_json", type=Path)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("backend/evaluation/fixtures/c26_misraj_source.json"),
    )
    parser.add_argument("--frontend", type=Path, default=Path("frontend"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.viewer_json.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    report = run_frug1_ingest_benchmark(
        payload,
        source,
        frontend_dir=args.frontend.resolve(),
    )
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
