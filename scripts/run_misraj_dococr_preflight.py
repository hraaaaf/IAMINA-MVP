from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from evaluation.misraj_dataset_preflight import summarize_misraj_viewer

DEFAULT_SOURCE = REPO_ROOT / "backend/evaluation/fixtures/c26_misraj_source.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("viewer_json", type=Path)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    payload = json.loads(args.viewer_json.read_text(encoding="utf-8"))
    result = summarize_misraj_viewer(
        payload,
        expected_total_rows=int(source["expected_total_rows"]),
        expected_features=list(source["expected_features"]),
        expected_first_uuid=str(source["expected_first_uuid"]),
    )
    result["source_contract"] = {
        "dataset": source["dataset"],
        "source_revision": source["source_revision"],
        "license": source["license"],
        "source_kind": source["source_kind"],
        "real_camera_claim": source["real_camera_claim"],
        "ground_truth": source["ground_truth"],
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
