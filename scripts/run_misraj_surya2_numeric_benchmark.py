from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from evaluation.surya2_numeric_benchmark import run_surya2_numeric_benchmark

SOURCE = REPO_ROOT / "backend/evaluation/fixtures/c26_misraj_source.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("viewer_json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    payload = json.loads(args.viewer_json.read_text(encoding="utf-8"))
    result = run_surya2_numeric_benchmark(payload, source)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["numeric_safety_floor_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
