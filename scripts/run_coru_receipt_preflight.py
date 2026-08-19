from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from evaluation.coru_dataset_preflight import summarize_coru_metadata

DEFAULT_SOURCE = REPO_ROOT / "backend/evaluation/fixtures/c25_coru_source.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("metadata", type=Path)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    result = summarize_coru_metadata(
        args.metadata,
        expected_sha256=str(source["expected_sha256"]),
    )
    result["source_contract"] = {
        "dataset": source["dataset"],
        "component": source["component"],
        "license": source["license"],
        "languages": source["languages"],
        "source_kind": source["source_kind"],
        "privacy_basis": source["privacy_basis"],
        "camera_provenance_claim": source["camera_provenance_claim"],
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
