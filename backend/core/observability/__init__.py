"""
core.observability — product telemetry layer.

Public surface:
  track()          — fire-and-forget DB event write
  EVT_*            — event type constants
  ClinicalLogger   — structured file-only technical logger (Phase 2)
"""

from .events import (
    EVT_CHAT_MESSAGE,
    EVT_INACTIVE_7D,
    EVT_LOG_CREATED,
    EVT_SESSION_START,
    EVT_STREAK_BROKEN,
    EVT_STREAK_CONTINUED,
    EVT_SUMMARY_VIEWED,
    track,
)
from .logging import ClinicalLogger
from .retention_sql import RetentionMetrics, compute_retention_metrics

__all__ = [
    "track",
    "EVT_LOG_CREATED",
    "EVT_SESSION_START",
    "EVT_CHAT_MESSAGE",
    "EVT_STREAK_CONTINUED",
    "EVT_STREAK_BROKEN",
    "EVT_SUMMARY_VIEWED",
    "EVT_INACTIVE_7D",
    "ClinicalLogger",
    "RetentionMetrics",
    "compute_retention_metrics",
]
