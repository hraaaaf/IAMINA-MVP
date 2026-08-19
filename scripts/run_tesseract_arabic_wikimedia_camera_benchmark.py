from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from evaluation.tesseract_arabic_camera_benchmark import (
    run_tesseract_arabic_camera_benchmark,
)
from evaluation.wikimedia_camera_fixture import materialize_wikimedia_camera_fixture

DEFAULT_SOURCES = (
    REPO_ROOT / "backend/evaluation/fixtures/c24w_wikimedia_camera_sources.json"
)


def run_benchmark(sources_path: Path) -> dict[str, object]:
    specs = json.loads(sources_path.read_text(encoding="utf-8"))
    if not isinstance(specs, list) or not specs:
        raise ValueError("C24-W sources must be a non-empty JSON list")

    cases: list[dict[str, object]] = []
    engine_versions: set[str] = set()
    with tempfile.TemporaryDirectory(prefix="iamina-c24w-") as tmp:
        temp_root = Path(tmp)
        for index, spec in enumerate(specs):
            if not isinstance(spec, dict):
                raise ValueError("every C24-W source entry must be an object")
            workspace = temp_root / f"source-{index}"
            manifest_path, provenance = materialize_wikimedia_camera_fixture(
                spec, workspace
            )
            result = run_tesseract_arabic_camera_benchmark(
                manifest_path,
                workspace,
            )
            engine_versions.add(str(result["engine_version"]))
            case = dict(result["cases"][0])
            case["provenance"] = provenance
            cases.append(case)

    safe_cases = sum(1 for case in cases if case["numeric_ok"])
    return {
        "benchmark": "c24w-wikimedia-real-camera-arabic-numeric-safety",
        "engine": "tesseract",
        "engine_versions": sorted(engine_versions),
        "language": "ara",
        "patient_data": False,
        "provider_api": False,
        "paid_inference": False,
        "network_source": "Wikimedia Commons public originals",
        "provenance_checked": True,
        "real_camera_only": True,
        "numeric_safe_cases": safe_cases,
        "numeric_total": len(cases),
        "numeric_safety_floor_passed": safe_cases == len(cases),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = run_benchmark(args.sources)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["numeric_safety_floor_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
