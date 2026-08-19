"""Privacy-safe structural preflight for a pinned Misraj-DocOCR viewer slice."""

from __future__ import annotations

import re
from typing import Any

_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_NUMBER_RE = re.compile(r"[0-9٠-٩۰-۹]")


class MisrajPreflightError(ValueError):
    pass


def summarize_misraj_viewer(
    payload: dict[str, Any],
    *,
    expected_total_rows: int,
    expected_features: list[str],
    expected_first_uuid: str,
) -> dict[str, object]:
    features = payload.get("features")
    rows = payload.get("rows")
    total = payload.get("num_rows_total")
    if not isinstance(features, list) or not isinstance(rows, list):
        raise MisrajPreflightError("viewer payload is missing features or rows")
    if total != expected_total_rows:
        raise MisrajPreflightError("Misraj row count drifted from pinned contract")

    feature_names = [
        str(item.get("name"))
        for item in features
        if isinstance(item, dict) and item.get("name") is not None
    ]
    if feature_names != expected_features:
        raise MisrajPreflightError("Misraj feature schema drifted from pinned contract")
    if not rows:
        raise MisrajPreflightError("Misraj viewer returned no rows")

    first = rows[0].get("row") if isinstance(rows[0], dict) else None
    if not isinstance(first, dict) or first.get("uuid") != expected_first_uuid:
        raise MisrajPreflightError("Misraj first-row UUID drifted from pinned contract")

    arabic_rows = 0
    numeric_rows = 0
    image_rows = 0
    for item in rows:
        row = item.get("row") if isinstance(item, dict) else None
        if not isinstance(row, dict):
            raise MisrajPreflightError("Misraj viewer row is malformed")
        markdown = row.get("markdown")
        if not isinstance(markdown, str):
            raise MisrajPreflightError("Misraj markdown ground truth is missing")
        if _ARABIC_RE.search(markdown):
            arabic_rows += 1
        if _NUMBER_RE.search(markdown):
            numeric_rows += 1
        if row.get("image") is not None:
            image_rows += 1

    return {
        "total_rows": total,
        "sampled_rows": len(rows),
        "features": feature_names,
        "first_uuid_matches": True,
        "arabic_ground_truth_rows": arabic_rows,
        "numeric_ground_truth_rows": numeric_rows,
        "image_rows": image_rows,
        "raw_ground_truth_emitted": False,
        "real_camera_claim": False,
        "iamina_patient_data": False,
    }
