from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ALLOWED_SOURCE_TYPES = {"human_test_speaker", "synthetic_tts"}
ALLOWED_ENCODINGS = {"wav_pcm_s16le", "m4a_aac", "webm_opus"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class FixtureManifestError(ValueError):
    pass


def _require_text(item: dict[str, object], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FixtureManifestError(f"{key} is required")
    return value.strip()


def _validate_repo_relative(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        raise FixtureManifestError("audio_fixture must be repository-relative without traversal")
    return path


def validate_manifest(manifest_path: Path, repo_root: Path) -> list[dict[str, object]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise FixtureManifestError("manifest must be a non-empty JSON list")

    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    validated: list[dict[str, object]] = []

    for raw in payload:
        if not isinstance(raw, dict):
            raise FixtureManifestError("every fixture entry must be an object")
        item = dict(raw)
        fixture_id = _require_text(item, "fixture_id")
        if fixture_id in seen_ids:
            raise FixtureManifestError(f"duplicate fixture_id: {fixture_id}")
        seen_ids.add(fixture_id)

        relative = _validate_repo_relative(_require_text(item, "audio_fixture"))
        audio_path = (repo_root / relative).resolve()
        root = repo_root.resolve()
        if root not in audio_path.parents and audio_path != root:
            raise FixtureManifestError("audio_fixture escapes repository root")
        if not audio_path.is_file():
            raise FixtureManifestError(f"missing audio fixture: {relative.as_posix()}")

        digest = _require_text(item, "audio_sha256")
        if not SHA256_RE.fullmatch(digest):
            raise FixtureManifestError("audio_sha256 must be 64 lowercase hex characters")
        actual = hashlib.sha256(audio_path.read_bytes()).hexdigest()
        if actual != digest:
            raise FixtureManifestError(f"SHA-256 mismatch for {fixture_id}")
        if digest in seen_hashes:
            raise FixtureManifestError("duplicate audio content is not an independent rendition")
        seen_hashes.add(digest)

        source_type = _require_text(item, "source_type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            raise FixtureManifestError(f"unsupported source_type: {source_type}")
        if source_type == "human_test_speaker" and item.get("consent_recorded") is not True:
            raise FixtureManifestError("human_test_speaker requires consent_recorded=true")
        if item.get("patient_data") is not False:
            raise FixtureManifestError("patient_data must be false")

        _require_text(item, "locale")
        _require_text(item, "reference_transcript")
        _require_text(item, "capture_profile")
        _require_text(item, "created_on")
        review_status = item.get("review_status")
        reviewed_by = item.get("reviewed_by")
        if not (isinstance(review_status, str) and review_status.strip()) and not (
            isinstance(reviewed_by, str) and reviewed_by.strip()
        ):
            raise FixtureManifestError("review_status or reviewed_by is required")

        encoding = _require_text(item, "encoding")
        if encoding not in ALLOWED_ENCODINGS:
            raise FixtureManifestError(f"unsupported encoding: {encoding}")

        for key in ("sample_rate_hz", "channels", "duration_ms"):
            value = item.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise FixtureManifestError(f"{key} must be a positive integer")

        critical = item.get("critical_tokens")
        concepts = item.get("required_concepts")
        if not critical and not concepts:
            raise FixtureManifestError("critical_tokens and/or required_concepts is required")

        validated.append(item)

    return validated


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
