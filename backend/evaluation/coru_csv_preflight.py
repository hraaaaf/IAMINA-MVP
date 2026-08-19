"""Privacy-safe structural discovery for CORU IE CSV metadata."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from pathlib import Path

_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_NUMBER_RE = re.compile(r"\d")


def summarize_coru_csv(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise ValueError("CORU CSV must have a header")

    columns = [str(name) for name in reader.fieldnames]
    row_count = 0
    nonempty = {name: 0 for name in columns}
    arabic = {name: 0 for name in columns}
    numeric = {name: 0 for name in columns}
    for row in reader:
        row_count += 1
        for name in columns:
            value = row.get(name) or ""
            if value:
                nonempty[name] += 1
            if _ARABIC_RE.search(value):
                arabic[name] += 1
            if _NUMBER_RE.search(value):
                numeric[name] += 1

    return {
        "sha256": sha256,
        "bytes": len(raw),
        "row_count": row_count,
        "columns": columns,
        "column_signals": {
            name: {
                "nonempty_rows": nonempty[name],
                "arabic_rows": arabic[name],
                "numeric_rows": numeric[name],
            }
            for name in columns
        },
        "raw_values_emitted": False,
        "iamina_patient_data": False,
        "camera_provenance_claim": False,
    }
