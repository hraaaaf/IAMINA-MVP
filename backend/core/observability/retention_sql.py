"""
core.observability.retention_sql — Staff-only retention & engagement KPIs.

Computes cohort retention rates (D1/D7/D30/D90), event funnel counts,
and companion engagement ratio using raw SQL against core_observabilityevent.

Design decisions:
- SQL-first, per ADR-0007 (never Python-computed KPIs).
- Dual-DB: PostgreSQL native INTERVAL; SQLite julianday() fallback.
- Frozen dataclass output; no ORM objects.
- Acquisition anchor: log_created event.
- Staff-only: caller must enforce is_staff before calling this module.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from django.db import connection

from core.observability.events import EVT_LOG_CREATED

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 1. RESULT STRUCTURE
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RetentionMetrics:
    """
    Immutable retention + engagement snapshot.

    Retention rates are fractions in [0.0, 1.0] or None when the cohort is
    too young to have had a meaningful retention window.  cohort_ready_dN is
    False whenever retention_dN is None.

    funnel_* fields count distinct patients who fired each event type at least
    once.  missing event types default to 0.

    chat_per_active_patient is None when there are no active patients
    (cohort_size == 0) or no chat_message events.
    """

    cohort_size: int
    retention_d1: Optional[float]
    retention_d7: Optional[float]
    retention_d30: Optional[float]
    retention_d90: Optional[float]
    cohort_ready_d1: bool
    cohort_ready_d7: bool
    cohort_ready_d30: bool
    cohort_ready_d90: bool
    funnel_session_start: int
    funnel_log_created: int
    funnel_chat_message: int
    funnel_summary_viewed: int
    chat_per_active_patient: Optional[float]
    computed_at: datetime


# ──────────────────────────────────────────────────────────────────────────────
# 2. SQL STRINGS
# ──────────────────────────────────────────────────────────────────────────────

# PostgreSQL: uses INTERVAL arithmetic.
# CTE first_log: find the earliest log_created per patient (acquisition date).
# CTE cohort: for each acquired patient, check if any event exists >= N days later.
# Final SELECT: count cohort, sum retention flags, average as a ratio.
_RETENTION_SQL_PG = """
WITH first_log AS (
    SELECT
        patient_id,
        MIN(timestamp) AS acquired_at
    FROM core_observabilityevent
    WHERE event_type = '{acq}'
    GROUP BY patient_id
),
cohort AS (
    SELECT
        f.patient_id,
        f.acquired_at,
        CASE WHEN EXISTS (
            SELECT 1 FROM core_observabilityevent e
            WHERE e.patient_id = f.patient_id
              AND e.timestamp >= f.acquired_at + INTERVAL '1 day'
        ) THEN 1 ELSE 0 END AS retained_d1,
        CASE WHEN EXISTS (
            SELECT 1 FROM core_observabilityevent e
            WHERE e.patient_id = f.patient_id
              AND e.timestamp >= f.acquired_at + INTERVAL '7 days'
        ) THEN 1 ELSE 0 END AS retained_d7,
        CASE WHEN f.acquired_at <= NOW() - INTERVAL '30 days' AND EXISTS (
            SELECT 1 FROM core_observabilityevent e
            WHERE e.patient_id = f.patient_id
              AND e.timestamp >= f.acquired_at + INTERVAL '30 days'
        ) THEN 1
             WHEN f.acquired_at <= NOW() - INTERVAL '30 days' THEN 0
             ELSE NULL END  AS retained_d30,
        CASE WHEN f.acquired_at <= NOW() - INTERVAL '90 days' AND EXISTS (
            SELECT 1 FROM core_observabilityevent e
            WHERE e.patient_id = f.patient_id
              AND e.timestamp >= f.acquired_at + INTERVAL '90 days'
        ) THEN 1
             WHEN f.acquired_at <= NOW() - INTERVAL '90 days' THEN 0
             ELSE NULL END  AS retained_d90
    FROM first_log f
)
SELECT
    COUNT(*)                                        AS cohort_size,
    ROUND(AVG(retained_d1::float)::numeric, 4)     AS retention_d1,
    ROUND(AVG(retained_d7::float)::numeric, 4)     AS retention_d7,
    ROUND(AVG(retained_d30::float)::numeric, 4)    AS retention_d30,
    ROUND(AVG(retained_d90::float)::numeric, 4)    AS retention_d90
FROM cohort
"""

# SQLite: uses julianday() arithmetic for date differences.
# AVG() over NULL values returns the average of non-null rows (correct semantics
# for d30/d90 where young patients are excluded).
_RETENTION_SQL_SQLITE = """
WITH first_log AS (
    SELECT
        patient_id,
        MIN(timestamp) AS acquired_at
    FROM core_observabilityevent
    WHERE event_type = '{acq}'
    GROUP BY patient_id
),
cohort AS (
    SELECT
        f.patient_id,
        f.acquired_at,
        CASE WHEN EXISTS (
            SELECT 1 FROM core_observabilityevent e
            WHERE e.patient_id = f.patient_id
              AND julianday(e.timestamp) - julianday(f.acquired_at) >= 1
        ) THEN 1 ELSE 0 END AS retained_d1,
        CASE WHEN EXISTS (
            SELECT 1 FROM core_observabilityevent e
            WHERE e.patient_id = f.patient_id
              AND julianday(e.timestamp) - julianday(f.acquired_at) >= 7
        ) THEN 1 ELSE 0 END AS retained_d7,
        CASE WHEN julianday('now') - julianday(f.acquired_at) >= 30 AND EXISTS (
            SELECT 1 FROM core_observabilityevent e
            WHERE e.patient_id = f.patient_id
              AND julianday(e.timestamp) - julianday(f.acquired_at) >= 30
        ) THEN 1
             WHEN julianday('now') - julianday(f.acquired_at) >= 30 THEN 0
             ELSE NULL END  AS retained_d30,
        CASE WHEN julianday('now') - julianday(f.acquired_at) >= 90 AND EXISTS (
            SELECT 1 FROM core_observabilityevent e
            WHERE e.patient_id = f.patient_id
              AND julianday(e.timestamp) - julianday(f.acquired_at) >= 90
        ) THEN 1
             WHEN julianday('now') - julianday(f.acquired_at) >= 90 THEN 0
             ELSE NULL END  AS retained_d90
    FROM first_log f
)
SELECT
    COUNT(*)                AS cohort_size,
    AVG(retained_d1 * 1.0) AS retention_d1,
    AVG(retained_d7 * 1.0) AS retention_d7,
    AVG(retained_d30)       AS retention_d30,
    AVG(retained_d90)       AS retention_d90
FROM cohort
"""

# Funnel query: count of DISTINCT patients per event type.
_FUNNEL_SQL = """
SELECT
    event_type,
    COUNT(DISTINCT patient_id) AS cnt
FROM core_observabilityevent
WHERE event_type IN ('session_start', '{acq}', 'chat_message', 'summary_viewed')
GROUP BY event_type
"""

# Engagement: chat messages per active patient (active = has any event in DB).
# chat_per_active_patient = total chat_message events / cohort_size.
# Returns NULL if there are no chat_message events.
_ENGAGEMENT_SQL = """
SELECT
    COUNT(*) AS total_chat_messages,
    COUNT(DISTINCT patient_id) AS active_patients
FROM core_observabilityevent
WHERE event_type = 'chat_message'
"""


# ──────────────────────────────────────────────────────────────────────────────
# 3. HELPER ACCESSORS (testable individually)
# ──────────────────────────────────────────────────────────────────────────────

def _retention_sql_pg() -> str:
    """Return the PostgreSQL retention CTE query string."""
    return _RETENTION_SQL_PG


def _retention_sql_sqlite() -> str:
    """Return the SQLite retention CTE query string."""
    return _RETENTION_SQL_SQLITE


def _funnel_sql() -> str:
    """Return the funnel GROUP BY query string."""
    return _FUNNEL_SQL


def _engagement_sql() -> str:
    """Return the engagement ratio query string."""
    return _ENGAGEMENT_SQL


# ──────────────────────────────────────────────────────────────────────────────
# 4. MAIN COMPUTATION
# ──────────────────────────────────────────────────────────────────────────────

def compute_retention_metrics(
    acquisition_event: str = EVT_LOG_CREATED,
) -> RetentionMetrics:
    """
    Execute all three SQL queries and return an immutable RetentionMetrics snapshot.

    Caller must enforce is_staff before calling this function.
    Raises on SQL exception after logging — caller should convert to HTTP 500.

    Args:
        acquisition_event: ObservabilityEvent type used as cohort acquisition anchor.
            Defaults to EVT_LOG_CREATED ("log_created"). Pass a module manifest's
            acquisition_event to scope retention to that module.

    Returns:
        RetentionMetrics with current values from core_observabilityevent.
    """
    if not acquisition_event or "'" in acquisition_event:
        raise ValueError(
            f"acquisition_event must be a non-empty string without quotes, got: {acquisition_event!r}"
        )
    try:
        # ── Retention query ────────────────────────────────────────────────────
        retention_sql = (
            _RETENTION_SQL_PG
            if connection.vendor == "postgresql"
            else _RETENTION_SQL_SQLITE
        ).format(acq=acquisition_event)
        with connection.cursor() as cursor:
            cursor.execute(retention_sql)
            row = cursor.fetchone()

        if row is None:
            cohort_size = 0
            r_d1 = r_d7 = r_d30 = r_d90 = None
        else:
            cohort_size = int(row[0] or 0)
            r_d1  = float(row[1]) if row[1] is not None else None
            r_d7  = float(row[2]) if row[2] is not None else None
            r_d30 = float(row[3]) if row[3] is not None else None
            r_d90 = float(row[4]) if row[4] is not None else None

        # cohort_ready logic:
        # d1/d7: ready as soon as cohort_size > 0 (any patient can return next day)
        # d30/d90: ready only when at least one patient has been in cohort >= 30/90 days
        #          (i.e., when the rate is not None)
        cohort_ready_d1  = cohort_size > 0
        cohort_ready_d7  = cohort_size > 0
        cohort_ready_d30 = r_d30 is not None
        cohort_ready_d90 = r_d90 is not None

        # When cohort is empty, all rates are None
        if cohort_size == 0:
            r_d1 = r_d7 = r_d30 = r_d90 = None
            cohort_ready_d1 = cohort_ready_d7 = cohort_ready_d30 = cohort_ready_d90 = False

        # ── Funnel query ───────────────────────────────────────────────────────
        with connection.cursor() as cursor:
            cursor.execute(_FUNNEL_SQL.format(acq=acquisition_event))
            funnel_rows = cursor.fetchall()

        # Key set is dynamic: the acquisition anchor may vary per module.
        funnel: dict[str, int] = {
            "session_start":   0,
            acquisition_event: 0,
            "chat_message":    0,
            "summary_viewed":  0,
        }
        for event_type, cnt in funnel_rows:
            if event_type in funnel:
                funnel[event_type] = int(cnt)

        # ── Engagement query ───────────────────────────────────────────────────
        with connection.cursor() as cursor:
            cursor.execute(_ENGAGEMENT_SQL)
            eng_row = cursor.fetchone()

        chat_per_active: Optional[float] = None
        if eng_row:
            total_chat = int(eng_row[0] or 0)
            int(eng_row[1] or 0)
            if cohort_size > 0 and total_chat > 0:
                chat_per_active = round(total_chat / cohort_size, 2)

        return RetentionMetrics(
            cohort_size=cohort_size,
            retention_d1=r_d1,
            retention_d7=r_d7,
            retention_d30=r_d30,
            retention_d90=r_d90,
            cohort_ready_d1=cohort_ready_d1,
            cohort_ready_d7=cohort_ready_d7,
            cohort_ready_d30=cohort_ready_d30,
            cohort_ready_d90=cohort_ready_d90,
            funnel_session_start=funnel["session_start"],
            funnel_log_created=funnel[acquisition_event],
            funnel_chat_message=funnel["chat_message"],
            funnel_summary_viewed=funnel["summary_viewed"],
            chat_per_active_patient=chat_per_active,
            computed_at=datetime.now(UTC),
        )

    except Exception:
        logger.exception("compute_retention_metrics failed")
        raise
