from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from evaluation.tesseract_arabic_camera_benchmark import (
    run_tesseract_arabic_camera_benchmark,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tesseract-bin", default="tesseract")
    args = parser.parse_args()

    result = run_tesseract_arabic_camera_benchmark(
        args.manifest,
        args.repo_root,
        tesseract_bin=args.tesseract_bin,
    )
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["numeric_safety_floor_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
