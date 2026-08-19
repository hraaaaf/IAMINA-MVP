"""Integrity/provenance contract for controlled OCR/vision image fixtures."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ALLOWED_SOURCE_TYPES = {"real_camera_test", "synthetic_render"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class MediaFixtureError(ValueError):
    pass


def _require_text(item: dict[str, object], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MediaFixtureError(f"{key} is required")
    return value.strip()


def validate_media_fixture_manifest(
    manifest_path: Path,
    repo_root: Path,
) -> list[dict[str, object]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise MediaFixtureError("manifest must be a non-empty JSON list")

    root = repo_root.resolve()
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    validated: list[dict[str, object]] = []

    for raw in payload:
        if not isinstance(raw, dict):
            raise MediaFixtureError("every media fixture entry must be an object")
        item = dict(raw)
        fixture_id = _require_text(item, "fixture_id")
        if fixture_id in seen_ids:
            raise MediaFixtureError(f"duplicate fixture_id: {fixture_id}")
        seen_ids.add(fixture_id)

        relative = Path(_require_text(item, "image_fixture"))
        if relative.is_absolute() or ".." in relative.parts:
            raise MediaFixtureError("image_fixture must be repository-relative without traversal")
        if relative.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise MediaFixtureError("unsupported image fixture extension")
        image_path = (root / relative).resolve()
        if root not in image_path.parents and image_path != root:
            raise MediaFixtureError("image_fixture escapes repository root")
        if not image_path.is_file():
            raise MediaFixtureError(f"missing image fixture: {relative.as_posix()}")

        digest = _require_text(item, "image_sha256")
        if not SHA256_RE.fullmatch(digest):
            raise MediaFixtureError("image_sha256 must be 64 lowercase hex characters")
        actual = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if actual != digest:
            raise MediaFixtureError(f"SHA-256 mismatch for {fixture_id}")
        if digest in seen_hashes:
            raise MediaFixtureError("duplicate image content is not independent evidence")
        seen_hashes.add(digest)

        source_type = _require_text(item, "source_type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            raise MediaFixtureError(f"unsupported source_type: {source_type}")
        if item.get("patient_data") is not False:
            raise MediaFixtureError("patient_data must be false")

        _require_text(item, "locale")
        _require_text(item, "reference_text")
        _require_text(item, "capture_profile")
        if source_type == "real_camera_test":
            _require_text(item, "capture_device")

        validated.append(item)

    return validated
