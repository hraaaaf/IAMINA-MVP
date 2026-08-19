from __future__ import annotations

from pathlib import Path

from evaluation.coru_csv_preflight import summarize_coru_csv


def test_coru_csv_preflight_emits_signals_without_raw_values(tmp_path: Path):
    path = tmp_path / "test.csv"
    path.write_text(
        "image,item,price\nsecret-1.jpg,سكر,54.25\nsecret-2.jpg,bread,12\n",
        encoding="utf-8",
    )

    result = summarize_coru_csv(path)

    assert result["row_count"] == 2
    assert result["columns"] == ["image", "item", "price"]
    assert result["column_signals"]["item"]["arabic_rows"] == 1
    assert result["column_signals"]["price"]["numeric_rows"] == 2
    assert result["raw_values_emitted"] is False
    rendered = str(result)
    assert "secret-1.jpg" not in rendered
    assert "سكر" not in rendered
    assert "54.25" not in rendered
