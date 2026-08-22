"""
Spreadsheet extractor — Phase 12 Document Pulper.

Handles bounded CSV, XLSX and legacy XLS glucose exports.
"""
from __future__ import annotations

import io
import logging
from typing import Dict, List, Optional, Tuple

from media.documents.security import DocumentSecurityError, validate_office_container

logger = logging.getLogger(__name__)

_GLUCOSE_MIN = 20.0
_GLUCOSE_MAX = 600.0
_MAX_ROWS = 100_000
_MAX_COLUMNS = 256
_MAX_SUMMARY_CHARS = 16_000

_LIBRELINK_GLUCOSE_COLS = [
    "historic glucose mg/dl", "scan glucose mg/dl",
    "glycémie historique mg/dl", "glycémie scannée mg/dl",
    "historic glucose mmol/l", "scan glucose mmol/l",
]
_LIBRELINK_TIME_COLS = ["device timestamp", "horodatage de l'appareil"]

_DEXCOM_GLUCOSE_COLS = ["glucose value (mg/dl)", "egv (mg/dl)"]
_DEXCOM_TIME_COLS = ["timestamp (yyyy-mm-ddthh:mm:ss)", "displaytime"]

_GENERIC_GLUCOSE_COLS = [
    "glucose", "glycemie", "glycémie", "blood sugar", "blood_sugar",
    "mg/dl", "mmol/l", "glukose", "glucosa",
]
_GENERIC_TIME_COLS = ["time", "date", "timestamp", "datetime", "horodatage", "heure"]


def extract_spreadsheet(file_bytes: bytes, filename: str) -> Tuple[List[Dict], str, str]:
    """Parse one bounded spreadsheet into normalized readings and a short summary."""
    try:
        import pandas as pd
    except ImportError:
        logger.error("spreadsheet_extractor: pandas unavailable")
        return [], "unknown", ""

    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "csv"

    try:
        if ext == "xlsx":
            validate_office_container(file_bytes, "xlsx")
            df = pd.read_excel(
                io.BytesIO(file_bytes),
                engine="openpyxl",
                nrows=_MAX_ROWS + 1,
            )
            source_row_offset = 2
        elif ext == "xls":
            df = pd.read_excel(
                io.BytesIO(file_bytes),
                engine="xlrd",
                nrows=_MAX_ROWS + 1,
            )
            source_row_offset = 2
        else:
            skip_rows = _detect_skip_rows(file_bytes)
            try:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding="utf-8",
                    skiprows=skip_rows,
                    nrows=_MAX_ROWS + 1,
                )
            except UnicodeDecodeError:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding="latin-1",
                    skiprows=skip_rows,
                    nrows=_MAX_ROWS + 1,
                )
            source_row_offset = skip_rows + 2

        if len(df) > _MAX_ROWS:
            raise DocumentSecurityError("spreadsheet_row_limit")
        if len(df.columns) > _MAX_COLUMNS:
            raise DocumentSecurityError("spreadsheet_column_limit")
    except DocumentSecurityError:
        raise
    except Exception as exc:
        logger.warning(
            "spreadsheet_extractor: parse failed error_class=%s",
            type(exc).__name__,
        )
        return [], "unknown", ""

    cols_lower = {str(column).lower().strip(): column for column in df.columns}
    preview = df.head(3).to_string()
    raw_summary = (
        f"Colonnes: {list(df.columns)}\nLignes: {len(df)}\nAperçu:\n{preview}"
    )[:_MAX_SUMMARY_CHARS]

    source_type, glucose_col, time_col, unit = _detect_format(cols_lower)

    if not glucose_col:
        logger.info(
            "spreadsheet_extractor: no glucose column found column_count=%d",
            len(cols_lower),
        )
        return [], source_type, raw_summary

    readings = _extract_readings(
        df,
        glucose_col,
        time_col,
        unit,
        source_row_offset=source_row_offset,
    )
    return readings, source_type, raw_summary


def _detect_skip_rows(file_bytes: bytes) -> int:
    """LibreLink CSVs can have metadata rows before the header."""
    text = file_bytes[:2000].decode("utf-8", errors="replace")
    for index, line in enumerate(text.splitlines()):
        if "glucose" in line.lower() or "glycémie" in line.lower():
            return index
    return 0


def _detect_format(cols_lower: dict) -> Tuple[str, Optional[str], Optional[str], str]:
    for lower_name in _LIBRELINK_GLUCOSE_COLS:
        if lower_name in cols_lower:
            unit = "mmol/L" if "mmol" in lower_name else "mg/dL"
            time_col = next(
                (cols_lower[name] for name in _LIBRELINK_TIME_COLS if name in cols_lower),
                None,
            )
            return "cgm_export", cols_lower[lower_name], time_col, unit

    for lower_name in _DEXCOM_GLUCOSE_COLS:
        if lower_name in cols_lower:
            time_col = next(
                (cols_lower[name] for name in _DEXCOM_TIME_COLS if name in cols_lower),
                None,
            )
            return "cgm_export", cols_lower[lower_name], time_col, "mg/dL"

    for lower_name in _GENERIC_GLUCOSE_COLS:
        if lower_name in cols_lower:
            unit = "mmol/L" if "mmol" in lower_name else "mg/dL"
            time_col = next(
                (cols_lower[name] for name in _GENERIC_TIME_COLS if name in cols_lower),
                None,
            )
            return "glucose_log", cols_lower[lower_name], time_col, unit

    return "unknown", None, None, "mg/dL"


def _to_mgdl(value: float, unit: str) -> float:
    if "mmol" in unit.lower():
        return round(value * 18.018, 1)
    return value


def _extract_readings(
    df,
    glucose_col: str,
    time_col: Optional[str],
    unit: str,
    *,
    source_row_offset: int = 2,
) -> List[Dict]:
    readings = []
    for row_index, (_, row) in enumerate(df.iterrows()):
        raw_val = row.get(glucose_col)
        if raw_val is None or str(raw_val).strip() in ("", "nan", "NaN"):
            continue
        try:
            val = float(str(raw_val).replace(",", "."))
        except (ValueError, TypeError):
            continue

        val_mgdl = _to_mgdl(val, unit)
        if not (_GLUCOSE_MIN <= val_mgdl <= _GLUCOSE_MAX):
            continue

        timestamp = None
        raw_timestamp = None
        if time_col and time_col in row:
            ts_raw = row[time_col]
            if ts_raw and str(ts_raw).strip() not in ("", "nan", "NaT"):
                raw_timestamp = str(ts_raw)
                timestamp = raw_timestamp

        readings.append({
            "value_mgdl": val_mgdl,
            "timestamp": timestamp,
            "context": None,
            "original_value": val,
            "original_unit": unit,
            "_source_row": source_row_offset + row_index,
            "_glucose_column": glucose_col,
            "_timestamp_column": time_col,
            "_raw_glucose": str(raw_val),
            "_raw_timestamp": raw_timestamp,
        })
    return readings
