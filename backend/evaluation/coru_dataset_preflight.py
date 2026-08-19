"""Privacy-safe structural preflight for the pinned CORU receipt metadata file."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class CoruPreflightError(ValueError):
    pass


def _item_keys(values: list[object], limit: int = 100) -> list[str]:
    keys: set[str] = set()
    for value in values[:limit]:
        if isinstance(value, dict):
            keys.update(str(key) for key in value)
    return sorted(keys)


def _shape(value: Any) -> dict[str, object]:
    if isinstance(value, dict):
        return {
            "type": "object",
            "key_count": len(value),
            "keys": sorted(str(key) for key in value),
        }
    if isinstance(value, list):
        return {
            "type": "array",
            "count": len(value),
            "sampled_item_keys": _item_keys(value),
            "sampled_item_types": sorted(
                {type(item).__name__ for item in value[:100]}
            ),
        }
    return {"type": type(value).__name__}


def summarize_coru_metadata(
    path: Path,
    *,
    expected_sha256: str,
) -> dict[str, object]:
    raw = path.read_bytes()
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise CoruPreflightError("CORU metadata SHA-256 does not match pinned source")

    payload = json.loads(raw.decode("utf-8"))
    if isinstance(payload, dict):
        sections = {str(key): _shape(value) for key, value in payload.items()}
        top_level = "object"
    elif isinstance(payload, list):
        sections = {"root": _shape(payload)}
        top_level = "array"
    else:
        raise CoruPreflightError("CORU metadata top level must be object or array")

    return {
        "dataset": "abdoelsayed/CORU",
        "component": "Receipt/test.json",
        "sha256": actual_sha256,
        "bytes": len(raw),
        "top_level_type": top_level,
        "sections": sections,
        "raw_values_emitted": False,
        "iamina_patient_data": False,
        "camera_provenance_claim": False,
    }
