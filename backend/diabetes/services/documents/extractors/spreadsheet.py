"""
Spreadsheet extractor — Phase 12 Document Pulper.

Handles: CSV, Excel (.xlsx / .xls)

Detection order (most specific first):
  1. LibreLink detailed format   → source_type = 'cgm_export'
  2. Dexcom Clarity format       → source_type = 'cgm_export'
  3. Medtronic CareLink format   → source_type = 'cgm_export'
  4. Generic glucose columns     → source_type = 'glucose_log'

Returns (readings: list[dict], source_type: str, raw_text: str)
  readings = [{'timestamp': str|None, 'value_mgdl': float, 'context': str|None}]
Private ``_source_*`` keys retain row/column evidence for Pulper provenance.
"""
from __future__ import annotations

import io
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_GLUCOSE_MIN = 20.0
_GLUCOSE_MAX = 600.0

# ── Column name patterns ──────────────────────────────────────────────────────

_LIBRELINK_GLUCOSE_COLS = [
    'historic glucose mg/dl', 'scan glucose mg/dl',
    'glycémie historique mg/dl', 'glycémie scannée mg/dl',
    'historic glucose mmol/l', 'scan glucose mmol/l',
]
_LIBRELINK_TIME_COLS    = ['device timestamp', 'horodatage de l\'appareil']

_DEXCOM_GLUCOSE_COLS    = ['glucose value (mg/dl)', 'egv (mg/dl)']
_DEXCOM_TIME_COLS       = ['timestamp (yyyy-mm-ddthh:mm:ss)', 'displaytime']

_GENERIC_GLUCOSE_COLS   = ['glucose', 'glycemie', 'glycémie', 'blood sugar', 'blood_sugar',
                           'mg/dl', 'mmol/l', 'glukose', 'glucosa']
_GENERIC_TIME_COLS      = ['time', 'date', 'timestamp', 'datetime', 'horodatage', 'heure']


def extract_spreadsheet(file_bytes: bytes, filename: str) -> Tuple[List[Dict], str, str]:
    """
    Parse a CSV or Excel file.

    Returns:
        (readings, source_type, raw_text_summary)
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not installed — spreadsheet extraction unavailable.")
        return [], 'unknown', ''

    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else 'csv'

    try:
        if ext in ('xlsx', 'xls'):
            df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl' if ext == 'xlsx' else 'xlrd')
            source_row_offset = 2
        else:
            # Try UTF-8 first, fallback to latin-1 (LibreLink exports)
            skip_rows = _detect_skip_rows(file_bytes)
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8', skiprows=skip_rows)
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin-1', skiprows=skip_rows)
            source_row_offset = skip_rows + 2
    except Exception as exc:
        logger.warning("spreadsheet_extractor: failed to parse file: %s", exc)
        return [], 'unknown', ''

    cols_lower = {c.lower().strip(): c for c in df.columns}
    raw_summary = f"Colonnes: {list(df.columns)}\nLignes: {len(df)}\nAperçu:\n{df.head(3).to_string()}"

    # ── Detect format ──────────────────────────────────────────────────────────
    source_type, glucose_col, time_col, unit = _detect_format(cols_lower)

    if not glucose_col:
        logger.info("spreadsheet_extractor: no glucose column found. Available: %s", list(cols_lower.keys()))
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
    """LibreLink CSVs have 1-2 metadata rows before the header."""
    try:
        text = file_bytes[:2000].decode('utf-8', errors='replace')
        for i, line in enumerate(text.splitlines()):
            if 'glucose' in line.lower() or 'glycémie' in line.lower():
                return i
        return 0
    except Exception:
        return 0


def _detect_format(cols_lower: dict) -> Tuple[str, Optional[str], Optional[str], str]:
    """Returns (source_type, glucose_col_original, time_col_original, unit)."""

    # LibreLink
    for lc in _LIBRELINK_GLUCOSE_COLS:
        if lc in cols_lower:
            unit = 'mmol/L' if 'mmol' in lc else 'mg/dL'
            tc = next((cols_lower[c] for c in _LIBRELINK_TIME_COLS if c in cols_lower), None)
            return 'cgm_export', cols_lower[lc], tc, unit

    # Dexcom
    for lc in _DEXCOM_GLUCOSE_COLS:
        if lc in cols_lower:
            tc = next((cols_lower[c] for c in _DEXCOM_TIME_COLS if c in cols_lower), None)
            return 'cgm_export', cols_lower[lc], tc, 'mg/dL'

    # Generic
    for lc in _GENERIC_GLUCOSE_COLS:
        if lc in cols_lower:
            unit = 'mmol/L' if 'mmol' in lc else 'mg/dL'
            tc = next((cols_lower[c] for c in _GENERIC_TIME_COLS if c in cols_lower), None)
            return 'glucose_log', cols_lower[lc], tc, unit

    return 'unknown', None, None, 'mg/dL'


def _to_mgdl(value: float, unit: str) -> float:
    if 'mmol' in unit.lower():
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
        if raw_val is None or str(raw_val).strip() in ('', 'nan', 'NaN'):
            continue
        try:
            val = float(str(raw_val).replace(',', '.'))
        except (ValueError, TypeError):
            continue

        val_mgdl = _to_mgdl(val, unit)
        if not (_GLUCOSE_MIN <= val_mgdl <= _GLUCOSE_MAX):
            continue

        ts = None
        raw_timestamp = None
        if time_col and time_col in row:
            ts_raw = row[time_col]
            if ts_raw and str(ts_raw).strip() not in ('', 'nan', 'NaT'):
                raw_timestamp = str(ts_raw)
                ts = raw_timestamp

        readings.append({
            'value_mgdl':     val_mgdl,
            'timestamp':      ts,
            'context':        None,
            'original_value': val,
            'original_unit':  unit,
            '_source_row':    source_row_offset + row_index,
            '_glucose_column': glucose_col,
            '_timestamp_column': time_col,
            '_raw_glucose':   str(raw_val),
            '_raw_timestamp': raw_timestamp,
        })
    return readings
