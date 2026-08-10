"""
core.observability.retention_sql — staff-only pilot retention & engagement KPIs.

Computes rolling cohort retention rates (D1/D7/D30/D90), event funnel counts,
and companion engagement ratio using raw SQL against core_observabilityevent.

Design decisions:
- SQL-first, per ADR-0007 (never Python-computed KPIs).
- Dual-DB: PostgreSQL native INTERVAL; SQLite julianday() fallback.
- Frozen dataclass output; no ORM objects.
- Acquisition anchor: log_created event by default.
- Rolling retention: a patient is retained at Dn after any return event at or
  after acquisition + n days and no later than the snapshot ``as_of`` time.
- Horizon denominators contain only patients old enough to reach that horizon.
- Snapshot queries are bounded by one explicit ``as_of`` timestamp so the same
  evidence cut can be reproduced later.
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

RETENTION_CONTRACT_VERSION = "2.0"
RETENTION_SEMANTICS = "rolling_return_on_or_after_horizon"


# ──────────────────────────────────────────────────────────────────────────────
# 1. RESULT STRUCTURE
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RetentionMetrics:
    """Immutable, auditable retention + engagement snapshot.

    ``cohort_size`` is the number of patients whose acquisition event happened
    on or before ``as_of``. ``eligible_dN`` is the denominator for that horizon:
    patients whose acquisition is at least N days old at ``as_of``.

    Retention rates are rolling fractions in [0.0, 1.0] or ``None`` when no
    patient is yet eligible for that horizon. ``cohort_ready_dN`` is therefore
    exactly equivalent to ``eligible_dN > 0``.

    ``funnel_*`` fields count distinct patients who fired each event type at
    least once on or before ``as_of``. Missing event types default to 0.

    ``chat_per_active_patient`` retains its historical product-engagement
    contract and is not a clinical metric.
    """

    cohort_size: int
    eligible_d1: int
    eligible_d7: int
    eligible_d30: int
    eligible_d90: int
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
    retention_contract_version: str
    retention_semantics: str
    as_of: datetime
    computed_at: datetime


# ──────────────────────────────────────────────────────────────────────────────
# 2. SQL STRINGS
# ──────────────────────────────────────────────────────────────────────────────

# PostgreSQL: one bound as_of timestamp drives acquisition eligibility, horizon
# maturity and return-event cutoff. AVG ignores NULL, so immature patients never
# enter a horizon denominator.
_RETENTION_SQL_PG = """
WITH params AS (
    SELECT %s::timestamptz AS as_of
),
first_log AS (
    SELECT
        e.patient_id,
        MIN(e.timestamp) AS acquired_at
    FROM core_observabilityevent e
    CROSS JOIN params p
    WHERE e.event_type = '{acq}'
      AND e.timestamp <= p.as_of
    GROUP BY e.patient_id
),
cohort AS (
    SELECT
        f.patient_id,
        f.acquired_at,
        CASE WHEN f.acquired_at <= p.as_of - INTERVAL '1 day' THEN
            CASE WHEN EXISTS (
                SELECT 1 FROM core_observabilityevent e
                WHERE e.patient_id = f.patient_id
                  AND e.timestamp >= f.acquired_at + INTERVAL '1 day'
                  AND e.timestamp <= p.as_of
            ) THEN 1 ELSE 0 END
        ELSE NULL END AS retained_d1,
        CASE WHEN f.acquired_at <= p.as_of - INTERVAL '7 days' THEN
            CASE WHEN EXISTS (
                SELECT 1 FROM core_observabilityevent e
                WHERE e.patient_id = f.patient_id
                  AND e.timestamp >= f.acquired_at + INTERVAL '7 days'
                  AND e.timestamp <= p.as_of
            ) THEN 1 ELSE 0 END
        ELSE NULL END AS retained_d7,
        CASE WHEN f.acquired_at <= p.as_of - INTERVAL '30 days' THEN
            CASE WHEN EXISTS (
                SELECT 1 FROM core_observabilityevent e
                WHERE e.patient_id = f.patient_id
                  AND e.timestamp >= f.acquired_at + INTERVAL '30 days'
                  AND e.timestamp <= p.as_of
            ) THEN 1 ELSE 0 END
        ELSE NULL END AS retained_d30,
        CASE WHEN f.acquired_at <= p.as_of - INTERVAL '90 days' THEN
            CASE WHEN EXISTS (
                SELECT 1 FROM core_observabilityevent e
                WHERE e.patient_id = f.patient_id
                  AND e.timestamp >= f.acquired_at + INTERVAL '90 days'
                  AND e.timestamp <= p.as_of
            ) THEN 1 ELSE 0 END
        ELSE NULL END AS retained_d90
    FROM first_log f
    CROSS JOIN params p
)
SELECT
    COUNT(*)                                        AS cohort_size,
    COUNT(retained_d1)                              AS eligible_d1,
    COUNT(retained_d7)                              AS eligible_d7,
    COUNT(retained_d30)                             AS eligible_d30,
    COUNT(retained_d90)                             AS eligible_d90,
    ROUND(AVG(retained_d1::float)::numeric, 4)     AS retention_d1,
    ROUND(AVG(retained_d7::float)::numeric, 4)     AS retention_d7,
    ROUND(AVG(retained_d30::float)::numeric, 4)    AS retention_d30,
    ROUND(AVG(retained_d90::float)::numeric, 4)    AS retention_d90
FROM cohort
"""

# SQLite: same contract using julianday() arithmetic. The as_of value is bound
# once through the params CTE, matching the PostgreSQL query shape.
_RETENTION_SQL_SQLITE = """
WITH params AS (
    SELECT %s AS as_of
),
first_log AS (
    SELECT
        e.patient_id,
        MIN(e.timestamp) AS acquired_at
    FROM core_observabilityevent e
    CROSS JOIN params p
    WHERE e.event_type = '{acq}'
      AND julianday(e.timestamp) <= julianday(p.as_of)
    GROUP BY e.patient_id
),
cohort AS (
    SELECT
        f.patient_id,
        f.acquired_at,
        CASE WHEN julianday(p.as_of) - julianday(f.acquired_at) >= 1 THEN
            CASE WHEN EXISTS (
                SELECT 1 FROM core_observabilityevent e
                WHERE e.patient_id = f.patient_id
                  AND julianday(e.timestamp) - julianday(f.acquired_at) >= 1
                  AND julianday(e.timestamp) <= julianday(p.as_of)
            ) THEN 1 ELSE 0 END
        ELSE NULL END AS retained_d1,
        CASE WHEN julianday(p.as_of) - julianday(f.acquired_at) >= 7 THEN
            CASE WHEN EXISTS (
                SELECT 1 FROM core_observabilityevent e
                WHERE e.patient_id = f.patient_id
                  AND julianday(e.timestamp) - julianday(f.acquired_at) >= 7
                  AND julianday(e.timestamp) <= julianday(p.as_of)
            ) THEN 1 ELSE 0 END
        ELSE NULL END AS retained_d7,
        CASE WHEN julianday(p.as_of) - julianday(f.acquired_at) >= 30 THEN
            CASE WHEN EXISTS (
                SELECT 1 FROM core_observabilityevent e
                WHERE e.patient_id = f.patient_id
                  AND julianday(e.timestamp) - julianday(f.acquired_at) >= 30
                  AND julianday(e.timestamp) <= julianday(p.as_of)
            ) THEN 1 ELSE 0 END
        ELSE NULL END AS retained_d30,
        CASE WHEN julianday(p.as_of) - julianday(f.acquired_at) >= 90 THEN
            CASE WHEN EXISTS (
                SELECT 1 FROM core_observabilityevent e
                WHERE e.patient_id = f.patient_id
                  AND julianday(e.timestamp) - julianday(f.acquired_at) >= 90
                  AND julianday(e.timestamp) <= julianday(p.as_of)
            ) THEN 1 ELSE 0 END
        ELSE NULL END AS retained_d90
    FROM first_log f
    CROSS JOIN params p
)
SELECT
    COUNT(*)                AS cohort_size,
    COUNT(retained_d1)      AS eligible_d1,
    COUNT(retained_d7)      AS eligible_d7,
    COUNT(retained_d30)     AS eligible_d30,
    COUNT(retained_d90)     AS eligible_d90,
    ROUND(AVG(retained_d1 * 1.0), 4)  AS retention_d1,
    ROUND(AVG(retained_d7 * 1.0), 4)  AS retention_d7,
    ROUND(AVG(retained_d30 * 1.0), 4) AS retention_d30,
    ROUND(AVG(retained_d90 * 1.0), 4) AS retention_d90
FROM cohort
"""

# Funnel query: count DISTINCT patients per event type, bounded by the same
# snapshot cutoff as retention.
_FUNNEL_SQL = """
SELECT
    event_type,
    COUNT(DISTINCT patient_id) AS cnt
FROM core_observabilityevent
WHERE event_type IN ('session_start', '{acq}', 'chat_message', 'summary_viewed')
  AND timestamp <= %s
GROUP BY event_type
"""

# Historical engagement query, now also bounded by as_of for reproducibility.
_ENGAGEMENT_SQL = """
SELECT
    COUNT(*) AS total_chat_messages,
    COUNT(DISTINCT patient_id) AS active_patients
FROM core_observabilityevent
WHERE event_type = 'chat_message'
  AND timestamp <= %s
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
    *,
    as_of: datetime | None = None,
) -> RetentionMetrics:
    """Return one reproducible retention/engagement evidence snapshot.

    Caller must enforce ``is_staff`` before calling this function. SQL errors are
    logged and re-raised for the caller to convert to an appropriate failure.

    Args:
        acquisition_event: event type used as the cohort acquisition anchor.
        as_of: timezone-aware evidence cutoff. Defaults to the current UTC time.
            Events after this timestamp cannot affect the returned snapshot.
    """
    if not acquisition_event or "'" in acquisition_event:
        raise ValueError(
            "acquisition_event must be a non-empty string without quotes, "
            f"got: {acquisition_event!r}"
        )

    snapshot_at = as_of or datetime.now(UTC)
    if snapshot_at.tzinfo is None or snapshot_at.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    snapshot_at = snapshot_at.astimezone(UTC)

    try:
        retention_sql = (
            _RETENTION_SQL_PG
            if connection.vendor == "postgresql"
            else _RETENTION_SQL_SQLITE
        ).format(acq=acquisition_event)
        with connection.cursor() as cursor:
            cursor.execute(retention_sql, [snapshot_at])
            row = cursor.fetchone()

        if row is None:
            cohort_size = 0
            eligible_d1 = eligible_d7 = eligible_d30 = eligible_d90 = 0
            r_d1 = r_d7 = r_d30 = r_d90 = None
        else:
            cohort_size = int(row[0] or 0)
            eligible_d1 = int(row[1] or 0)
            eligible_d7 = int(row[2] or 0)
            eligible_d30 = int(row[3] or 0)
            eligible_d90 = int(row[4] or 0)
            r_d1 = float(row[5]) if row[5] is not None else None
            r_d7 = float(row[6]) if row[6] is not None else None
            r_d30 = float(row[7]) if row[7] is not None else None
            r_d90 = float(row[8]) if row[8] is not None else None

        cohort_ready_d1 = eligible_d1 > 0
        cohort_ready_d7 = eligible_d7 > 0
        cohort_ready_d30 = eligible_d30 > 0
        cohort_ready_d90 = eligible_d90 > 0

        with connection.cursor() as cursor:
            cursor.execute(_FUNNEL_SQL.format(acq=acquisition_event), [snapshot_at])
            funnel_rows = cursor.fetchall()

        funnel: dict[str, int] = {
            "session_start": 0,
            acquisition_event: 0,
            "chat_message": 0,
            "summary_viewed": 0,
        }
        for event_type, cnt in funnel_rows:
            if event_type in funnel:
                funnel[event_type] = int(cnt)

        with connection.cursor() as cursor:
            cursor.execute(_ENGAGEMENT_SQL, [snapshot_at])
            eng_row = cursor.fetchone()

        chat_per_active: Optional[float] = None
        if eng_row:
            total_chat = int(eng_row[0] or 0)
            if cohort_size > 0 and total_chat > 0:
                chat_per_active = round(total_chat / cohort_size, 2)

        return RetentionMetrics(
            cohort_size=cohort_size,
            eligible_d1=eligible_d1,
            eligible_d7=eligible_d7,
            eligible_d30=eligible_d30,
            eligible_d90=eligible_d90,
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
            retention_contract_version=RETENTION_CONTRACT_VERSION,
            retention_semantics=RETENTION_SEMANTICS,
            as_of=snapshot_at,
            computed_at=datetime.now(UTC),
        )
    except Exception:
        logger.exception("compute_retention_metrics failed")
        raise
