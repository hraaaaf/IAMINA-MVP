"""
IAmina Router — Rules-based Input Dispatcher
=============================================
Classifies patient input into one of 4 modes (< 5ms, zero LLM cost):

  1. URGENT   → State machine (offline, < 50ms)
  2. SIMPLE   → Python template (post-log reaction, no LLM)
  3. SUMMARY  → LLM (narrative summary, weekly/monthly)
  4. CHAT     → LLM with full memory (open questions, correlations)

Design rationale (from Bilan Stratégique Mai 2026):
  - 65% of interactions are SIMPLE → no LLM call, no cost.
  - URGENT never touches the LLM → patient safety offline.

Fusion of engine/services/llm/router.py and engine/services/iamina/router.py (D1).
Public API: IaminaMode, RoutingResult, route()
classify() from iamina/router.py was dropped — no external callers confirmed.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class IaminaMode(Enum):
    URGENT = "urgent"
    SIMPLE = "simple"
    SUMMARY = "summary"
    CHAT = "chat"


@dataclass
class RoutingResult:
    mode: IaminaMode
    confidence: float
    reason: str
    extracted_value: Optional[float] = None


# ADA reference defaults — capsule callers should override via route() parameters.
_DEFAULT_URGENCY_LOW  = 54.0
_DEFAULT_URGENCY_HIGH = 300.0

# ── Regex patterns for glucose extraction ──
_GLUCOSE_PATTERN = re.compile(
    r'(?:glyc[eé]mie|glycemie|glucose|sucre|taux|g/l|mg/dl|dextro)\s*'
    r'[:=\s]*'
    r'(\d+[.,]?\d*)',
    re.IGNORECASE,
)

# ── Simple interaction keywords (post-log confirmations only — NOT greetings) ──
# NOTE: greetings (bonjour, salam, hey…) are intentionally excluded here so the
# LLM can give a warm, personalised reply instead of a canned message.
_SIMPLE_PATTERNS = [
    re.compile(r'^(oui|non|c\'est fait|noté|enregistré|ok|d\'accord)', re.IGNORECASE),
    re.compile(r'j\'ai\s+(mangé|pris|fait|bu|marché)', re.IGNORECASE),
]

# ── Summary trigger keywords ──
_SUMMARY_PATTERNS = [
    re.compile(r'(résumé|bilan|semaine|mois|rapport|recap|tendance|évolution)', re.IGNORECASE),
]


def route(
    user_input: str,
    latest_glucose: Optional[float] = None,
    urgency_low: float = _DEFAULT_URGENCY_LOW,
    urgency_high: float = _DEFAULT_URGENCY_HIGH,
) -> RoutingResult:
    """
    Classify user input into one of 4 IAmina modes.
    Total execution time target: < 5ms.

    Args:
        urgency_low:  Hypoglycemia threshold — pass DomainConfig.urgency_low.
        urgency_high: Hyperglycemia threshold — pass DomainConfig.urgency_high.
    """
    text = user_input.strip()

    if not text:
        return RoutingResult(
            mode=IaminaMode.SIMPLE,
            confidence=1.0,
            reason="empty_input",
        )

    # ── Priority 1: Urgency check (glucose values in text) ──
    glucose_match = _GLUCOSE_PATTERN.search(text)
    if glucose_match:
        try:
            value = float(glucose_match.group(1).replace(',', '.'))
            if value < urgency_low:
                return RoutingResult(
                    mode=IaminaMode.URGENT,
                    confidence=1.0,
                    reason=f"hypo_severe_{value}",
                    extracted_value=value,
                )
            if value > urgency_high:
                return RoutingResult(
                    mode=IaminaMode.URGENT,
                    confidence=1.0,
                    reason=f"hyper_severe_{value}",
                    extracted_value=value,
                )
        except ValueError:
            pass

    # ── Priority 1b: Urgency from latest_glucose (API context) ──
    if latest_glucose is not None:
        if latest_glucose < urgency_low:
            return RoutingResult(
                mode=IaminaMode.URGENT,
                confidence=1.0,
                reason=f"context_hypo_{latest_glucose}",
                extracted_value=latest_glucose,
            )
        if latest_glucose > urgency_high:
            return RoutingResult(
                mode=IaminaMode.URGENT,
                confidence=1.0,
                reason=f"context_hyper_{latest_glucose}",
                extracted_value=latest_glucose,
            )

    # ── Priority 2: Summary request ──
    for pattern in _SUMMARY_PATTERNS:
        if pattern.search(text):
            return RoutingResult(
                mode=IaminaMode.SUMMARY,
                confidence=0.9,
                reason="summary_keyword_match",
            )

    # ── Priority 3: Simple interaction (greetings, confirmations, post-log) ──
    for pattern in _SIMPLE_PATTERNS:
        if pattern.search(text):
            return RoutingResult(
                mode=IaminaMode.SIMPLE,
                confidence=0.85,
                reason="simple_pattern_match",
            )

    # NOTE: The old "< 15 chars → SIMPLE" heuristic was removed because it incorrectly
    # swallowed greetings like "bonjour", "salam", "salut !" — short but deserving a
    # warm LLM reply. The _SIMPLE_PATTERNS above already cover real acknowledgements
    # (ok, oui, non, c'est fait…). Everything else falls through to CHAT.

    # ── Default: Complex → LLM Chat ──
    return RoutingResult(
        mode=IaminaMode.CHAT,
        confidence=0.6,
        reason="default_to_chat",
    )
