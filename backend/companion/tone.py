"""
IAmina Tone Adapter
===================
P3 separates relationship tone from clinical truth. Conversation uses the
relationship-only selector below; modules remain responsible for clinical
semantics and thresholds.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ToneMode(Enum):
    ENCOURAGEANT = "encourageant"
    DOUX = "doux"
    CHALLENGE = "challenge"


@dataclass
class ToneContext:
    mode: ToneMode
    reason: str


def select_relationship_tone(
    *,
    emotional: bool = False,
    streak_days: int = 0,
) -> ToneContext:
    """Select tone from relationship signals only, never clinical thresholds."""
    if emotional:
        return ToneContext(mode=ToneMode.DOUX, reason="emotional_signal")
    if streak_days >= 7:
        return ToneContext(mode=ToneMode.ENCOURAGEANT, reason=f"streak_{streak_days}")
    return ToneContext(mode=ToneMode.ENCOURAGEANT, reason="relationship_default")


def select_tone(
    tir_pct: Optional[float] = None,
    cv_pct: Optional[float] = None,
    recent_hypos: int = 0,
    streak_days: int = 0,
) -> ToneContext:
    """Compatibility wrapper retained for callers outside P3 conversation runtime.

    Clinical arguments are intentionally ignored here. The chassis no longer
    interprets diabetes thresholds to choose conversational tone.
    """
    del tir_pct, cv_pct, recent_hypos
    return select_relationship_tone(streak_days=streak_days)


def get_tone_instruction(tone: ToneContext) -> str:
    """Return the prompt modifier for the selected relationship tone."""
    instructions = {
        ToneMode.ENCOURAGEANT: (
            "TONE: Be warm and encouraging. Acknowledge effort and continuity. "
            "Do not infer clinical progress from tone alone."
        ),
        ToneMode.DOUX: (
            "TONE: Be gentle and empathetic. Acknowledge difficulty without judgment. "
            "Do not introduce clinical conclusions or treatment advice."
        ),
        ToneMode.CHALLENGE: (
            "TONE: Be calmly motivating without creating medical goals or treatment actions."
        ),
    }
    return instructions.get(tone.mode, instructions[ToneMode.ENCOURAGEANT])
