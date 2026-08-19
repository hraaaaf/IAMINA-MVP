from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from evaluation.coru_dataset_preflight import CoruPreflightError, summarize_coru_metadata


def test_coru_preflight_reports_structure_without_raw_values(tmp_path: Path):
    payload = {
        "images": [{"id": 1, "file_name": "private-looking-name.jpg"}],
        "annotations": [{"image_id": 1, "category_id": 2, "secret": "do-not-emit"}],
        "categories": [{"id": 2, "name": "total"}],
    }
    path = tmp_path / "test.json"
    raw = json.dumps(payload).encode()
    path.write_bytes(raw)

    result = summarize_coru_metadata(
        path,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )

    assert result["top_level_type"] == "object"
    assert result["raw_values_emitted"] is False
    assert result["sections"]["images"]["count"] == 1
    assert result["sections"]["images"]["sampled_item_keys"] == ["file_name", "id"]
    rendered = json.dumps(result)
    assert "private-looking-name.jpg" not in rendered
    assert "do-not-emit" not in rendered


def test_coru_preflight_rejects_source_hash_drift(tmp_path: Path):
    path = tmp_path / "test.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(CoruPreflightError, match="SHA-256"):
        summarize_coru_metadata(path, expected_sha256="0" * 64)


def test_coru_preflight_accepts_array_top_level(tmp_path: Path):
    path = tmp_path / "test.json"
    raw = json.dumps([{"image": "x", "label": "y"}]).encode()
    path.write_bytes(raw)

    result = summarize_coru_metadata(
        path,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )

    assert result["top_level_type"] == "array"
    assert result["sections"]["root"]["sampled_item_keys"] == ["image", "label"]
