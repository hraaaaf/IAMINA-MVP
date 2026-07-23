"""
LibreLink / LibreView CSV Parser
================================
Parses CSV exports from Abbott FreeStyle LibreLink / LibreView accounts.

Two formats supported:

  FORMAT A — LibreView "Detailed" export (most common, English/French):
      Device,Serial Number,Device Timestamp,Record Type,Historic Glucose mg/dL,Scan Glucose mg/dL,...
      LibreView,12345,11-05-2026 08:30,0,150,,,,,,,,
      LibreView,12345,11-05-2026 08:45,1,,162,,,,,,,

  FORMAT B — Simplified glucose-only export:
      Device Timestamp,Glucose Value,Glucose Unit
      11/05/2026 08:30,150,mg/dL

Anti-hallucination: same validation pipeline as lab_parser. Values outside
physiological range (20-600 mg/dL) are silently dropped.

Output: list[LibreReading] ready for bulk LogEntry.create().
"""
from __future__ import annotations

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


# ── Physiological bounds ──────────────────────────────────────────────────────

_GLUCOSE_MIN_MGDL = 20.0
_GLUCOSE_MAX_MGDL = 600.0
_GLUCOSE_MIN_MMOL = 1.1
_GLUCOSE_MAX_MMOL = 33.3


# ── Output dataclasses ────────────────────────────────────────────────────────

@dataclass
class LibreReading:
    timestamp:    datetime
    glucose_mgdl: float
    record_type:  str = "historic"   # "historic" | "scan" | "strip" | "manual"


@dataclass
class LibreLinkParseResult:
    readings:        list[LibreReading] = field(default_factory=list)
    skipped_rows:    int = 0
    rejected_values: int = 0   # out-of-range
    detected_format: str = "unknown"
    detected_unit:   str = "mg/dL"
    error:           Optional[str] = None

    @property
    def total_parsed(self) -> int:
        return len(self.readings)


# ── Date parsing — LibreLink uses several formats depending on locale ────────

_DATE_FORMATS = [
    "%d-%m-%Y %H:%M",      # 11-05-2026 08:30 (LibreView FR/most EU)
    "%d/%m/%Y %H:%M",      # 11/05/2026 08:30 (LibreView FR alt)
    "%m-%d-%Y %I:%M %p",   # 05-11-2026 08:30 AM (LibreView US)
    "%m/%d/%Y %I:%M %p",
    "%Y-%m-%d %H:%M",      # ISO-ish
    "%Y-%m-%dT%H:%M",      # ISO 8601
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
]


def _parse_timestamp(s: str) -> Optional[datetime]:
    s = s.strip().strip('"')
    if not s:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _parse_glucose(s: str, unit: str) -> Optional[float]:
    s = s.strip().strip('"').replace(",", ".")
    if not s:
        return None
    try:
        val = float(s)
    except ValueError:
        return None
    # Convert mmol/L → mg/dL if needed (×18)
    if unit.lower().startswith("mmol"):
        if not (_GLUCOSE_MIN_MMOL <= val <= _GLUCOSE_MAX_MMOL):
            return None
        val = round(val * 18.0, 1)
    if not (_GLUCOSE_MIN_MGDL <= val <= _GLUCOSE_MAX_MGDL):
        return None
    return val


# ── Header detection ──────────────────────────────────────────────────────────

# LibreView detailed format markers
_FORMAT_A_MARKERS = {
    "device timestamp", "historic glucose mg/dl",
    "horodatage de l'appareil", "glucose historique mg/dl",
}

# Generic glucose CSV markers
_FORMAT_B_MARKERS = {"glucose value", "glucose", "valeur de glucose", "glycemie"}


def _detect_format(header: list[str]) -> str:
    lower = {h.strip().lower() for h in header}
    # Simple format wins if Glucose Value/Unit explicit (avoids ambiguity with
    # LibreLink "Device Timestamp" which appears in both)
    if lower & _FORMAT_B_MARKERS:
        return "simple"
    if lower & _FORMAT_A_MARKERS:
        return "librelink_detailed"
    return "unknown"


def _find_col(header: list[str], *candidates: str) -> Optional[int]:
    """Find first matching column index (case-insensitive)."""
    lower = [h.strip().lower() for h in header]
    for cand in candidates:
        c = cand.lower()
        for i, h in enumerate(lower):
            if h == c:
                return i
    return None


# ── Public API ────────────────────────────────────────────────────────────────

def parse_librelink_csv(csv_text: str) -> LibreLinkParseResult:
    """
    Parse a LibreLink / LibreView CSV export. Auto-detects format.

    Anti-hallucination guarantees:
      - Out-of-range glucose values are silently dropped
      - Unparseable timestamps are skipped
      - Returns explicit counts so caller can surface issues to user
    """
    result = LibreLinkParseResult()
    if not csv_text or not csv_text.strip():
        result.error = "empty_csv"
        return result

    # LibreView exports often have a 2-3 line header block before the actual
    # header row. Skip lines until we find a row with >= 4 commas/tabs.
    lines = csv_text.splitlines()
    header_idx = -1
    for i, line in enumerate(lines):
        # Need at least 2 separators (= 3 columns: timestamp, glucose, unit)
        if line.count(",") >= 2 or line.count(";") >= 2 or line.count("\t") >= 2:
            lower = line.lower()
            if any(m in lower for m in (
                "device timestamp", "horodatage", "glucose", "glycemie", "glycémie"
            )):
                header_idx = i
                break

    if header_idx < 0:
        result.error = "no_header_found"
        return result

    # Detect delimiter (comma vs semicolon)
    sample = lines[header_idx]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","

    rows = csv.reader(lines[header_idx:], delimiter=delimiter)
    try:
        header = next(rows)
    except StopIteration:
        result.error = "no_data"
        return result

    result.detected_format = _detect_format(header)

    if result.detected_format == "librelink_detailed":
        result.readings = list(_parse_librelink_detailed(rows, header, result))
    elif result.detected_format == "simple":
        result.readings = list(_parse_simple(rows, header, result))
    else:
        result.error = "unknown_format"
        return result

    logger.info(
        "librelink_parser: format=%s readings=%d skipped=%d rejected=%d",
        result.detected_format, len(result.readings),
        result.skipped_rows, result.rejected_values,
    )
    return result


# ── Format A: LibreView detailed ──────────────────────────────────────────────

def _parse_librelink_detailed(
    rows: Iterator[list[str]],
    header: list[str],
    result: LibreLinkParseResult,
) -> Iterator[LibreReading]:
    """
    LibreView 'Detailed' export columns (varies by language):
      - Device Timestamp / Horodatage
      - Record Type:  0=historic, 1=scan, 2=strip, 3=insulin, 4=manual carb...
      - Historic Glucose mg/dL  (Record Type 0)
      - Scan Glucose mg/dL      (Record Type 1)
      - Strip Glucose mg/dL     (Record Type 2)
    """
    ts_col   = _find_col(header, "Device Timestamp", "Horodatage de l'appareil")
    rt_col   = _find_col(header, "Record Type", "Type d'enregistrement")
    hist_col = _find_col(header, "Historic Glucose mg/dL", "Glucose historique mg/dL")
    scan_col = _find_col(header, "Scan Glucose mg/dL", "Glucose lu mg/dL")
    strip_col = _find_col(header, "Strip Glucose mg/dL", "Glucose bandelette mg/dL")

    if ts_col is None or (hist_col is None and scan_col is None):
        result.error = "required_columns_missing"
        return

    for row in rows:
        if not row or len(row) <= ts_col:
            result.skipped_rows += 1
            continue

        ts = _parse_timestamp(row[ts_col])
        if ts is None:
            result.skipped_rows += 1
            continue

        # Try historic → scan → strip in priority order (CGM first, BGM last)
        glucose: Optional[float] = None
        record_type = "historic"
        for col, label in (
            (hist_col,  "historic"),
            (scan_col,  "scan"),
            (strip_col, "strip"),
        ):
            if col is not None and col < len(row):
                v = _parse_glucose(row[col], "mg/dL")
                if v is not None:
                    glucose = v
                    record_type = label
                    break

        if glucose is None:
            # No valid glucose value in this row — could be a non-glucose record (insulin, carb)
            if (rt_col is not None and rt_col < len(row) and row[rt_col].strip() in ("0", "1", "2")):
                result.rejected_values += 1
            else:
                result.skipped_rows += 1
            continue

        yield LibreReading(timestamp=ts, glucose_mgdl=glucose, record_type=record_type)


# ── Format B: simple generic CSV ──────────────────────────────────────────────

def _parse_simple(
    rows: Iterator[list[str]],
    header: list[str],
    result: LibreLinkParseResult,
) -> Iterator[LibreReading]:
    ts_col = _find_col(header, "Device Timestamp", "Timestamp", "Date", "Horodatage")
    g_col  = _find_col(header, "Glucose Value", "Glucose", "Glycémie", "Glycemie")
    u_col  = _find_col(header, "Glucose Unit", "Unit", "Unité")

    if ts_col is None or g_col is None:
        result.error = "required_columns_missing"
        return

    # Default unit from first non-empty unit cell, else mg/dL
    default_unit = "mg/dL"

    for row in rows:
        if not row or len(row) <= max(ts_col, g_col):
            result.skipped_rows += 1
            continue

        ts = _parse_timestamp(row[ts_col])
        if ts is None:
            result.skipped_rows += 1
            continue

        unit = default_unit
        if u_col is not None and u_col < len(row):
            cell = row[u_col].strip()
            if cell:
                unit = cell
                if "mmol" in unit.lower():
                    result.detected_unit = "mmol/L"

        glucose = _parse_glucose(row[g_col], unit)
        if glucose is None:
            result.rejected_values += 1
            continue

        yield LibreReading(timestamp=ts, glucose_mgdl=glucose, record_type="historic")
