from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from evaluation.baseer_numeric_benchmark import (
    baseer_runtime_error_evidence,
    run_baseer_numeric_benchmark_diagnostic,
)

SOURCE = REPO_ROOT / "backend/evaluation/fixtures/c26_misraj_source.json"


def _write_result(path: Path, result: dict[str, object]) -> None:
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("viewer_json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        source = json.loads(SOURCE.read_text(encoding="utf-8"))
        payload = json.loads(args.viewer_json.read_text(encoding="utf-8"))
    except Exception as exc:
        result = baseer_runtime_error_evidence(phase="fixture_load", exc=exc)
        _write_result(args.output, result)
        return 2

    result = run_baseer_numeric_benchmark_diagnostic(payload, source)
    _write_result(args.output, result)
    return {"pass": 0, "verdict_reject": 1, "runtime_error": 2}[
        str(result["execution_outcome"])
    ]


if __name__ == "__main__":
    raise SystemExit(main())
