from __future__ import annotations

import pytest

from evaluation.misraj_dataset_preflight import (
    MisrajPreflightError,
    summarize_misraj_viewer,
)


def _payload() -> dict[str, object]:
    return {
        "features": [
            {"name": "uuid"},
            {"name": "markdown"},
            {"name": "image"},
        ],
        "rows": [
            {
                "row": {
                    "uuid": "expected-uuid",
                    "markdown": "فحص ٥٤",
                    "image": {"src": "redacted"},
                }
            },
            {
                "row": {
                    "uuid": "second",
                    "markdown": "نص عربي",
                    "image": {"src": "redacted-2"},
                }
            },
        ],
        "num_rows_total": 400,
    }


def test_misraj_preflight_reports_signals_without_raw_ground_truth():
    result = summarize_misraj_viewer(
        _payload(),
        expected_total_rows=400,
        expected_features=["uuid", "markdown", "image"],
        expected_first_uuid="expected-uuid",
    )

    assert result["arabic_ground_truth_rows"] == 2
    assert result["numeric_ground_truth_rows"] == 1
    assert result["image_rows"] == 2
    assert result["raw_ground_truth_emitted"] is False
    rendered = str(result)
    assert "فحص" not in rendered
    assert "redacted" not in rendered


def test_misraj_preflight_rejects_row_count_schema_or_uuid_drift():
    with pytest.raises(MisrajPreflightError, match="row count"):
        summarize_misraj_viewer(
            _payload(),
            expected_total_rows=401,
            expected_features=["uuid", "markdown", "image"],
            expected_first_uuid="expected-uuid",
        )

    with pytest.raises(MisrajPreflightError, match="feature schema"):
        summarize_misraj_viewer(
            _payload(),
            expected_total_rows=400,
            expected_features=["uuid", "image", "markdown"],
            expected_first_uuid="expected-uuid",
        )

    with pytest.raises(MisrajPreflightError, match="first-row UUID"):
        summarize_misraj_viewer(
            _payload(),
            expected_total_rows=400,
            expected_features=["uuid", "markdown", "image"],
            expected_first_uuid="other",
        )
