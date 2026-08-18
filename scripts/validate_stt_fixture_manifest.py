from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.stt_fixture_manifest import validate_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    validated = validate_manifest(args.manifest, args.repo_root)
    print(json.dumps({"validated_fixtures": len(validated)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
