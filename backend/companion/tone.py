"""
IAmina Tone Adapter
===================
Adapts the final response tone based on patient context and clinical state.

Three modes (from Bilan Stratégique Mai 2026):
  - ENCOURAGEANT: Patient is progressing well → celebrate, reinforce.
  - DOUX: Patient is struggling or emotional → soften, empathize.
  - CHALLENGE: Patient is stable but could do better → gently push.
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


# ── Tone selection thresholds ──
TIR_GOOD_THRESHOLD = 70.0      # % Time In Range → encouraging
TIR_STRUGGLE_THRESHOLD = 40.0  # % Time In Range → soft/gentle
CV_STABLE_THRESHOLD = 36.0     # % CV → stable variability


def select_tone(
    tir_pct: Optional[float] = None,
    cv_pct: Optional[float] = None,
    recent_hypos: int = 0,
    streak_days: int = 0,
) -> ToneContext:
    """
    Selects the appropriate tone for IAmina's response.
    Pure Python, < 1ms execution.
    """
    # Emotional safety first: recent hypos → always gentle
    if recent_hypos >= 2:
        return ToneContext(
            mode=ToneMode.DOUX,
            reason=f"recent_hypos_{recent_hypos}",
        )

    # Good TIR + logging streak → celebrate
    if tir_pct is not None and tir_pct >= TIR_GOOD_THRESHOLD:
        if streak_days >= 3:
            return ToneContext(
                mode=ToneMode.ENCOURAGEANT,
                reason=f"good_tir_{tir_pct:.0f}_streak_{streak_days}",
            )
        return ToneContext(
            mode=ToneMode.ENCOURAGEANT,
            reason=f"good_tir_{tir_pct:.0f}",
        )

    # Struggling TIR → soften
    if tir_pct is not None and tir_pct < TIR_STRUGGLE_THRESHOLD:
        return ToneContext(
            mode=ToneMode.DOUX,
            reason=f"low_tir_{tir_pct:.0f}",
        )

    # Stable but room for improvement → challenge
    if cv_pct is not None and cv_pct <= CV_STABLE_THRESHOLD:
        return ToneContext(
            mode=ToneMode.CHALLENGE,
            reason=f"stable_cv_{cv_pct:.0f}_room_to_grow",
        )

    # Default: encouraging
    return ToneContext(
        mode=ToneMode.ENCOURAGEANT,
        reason="default_encouraging",
    )


def get_tone_instruction(tone: ToneContext) -> str:
    """
    Returns the system prompt modifier for the selected tone.
    Appended to the LLM system instruction.
    """
    instructions = {
        ToneMode.ENCOURAGEANT: (
            "TONE: Be warm and encouraging. Celebrate progress, no matter how small. "
            "Use positive reinforcement. Highlight what the patient is doing well. "
            "Example: 'Bravo pour ta régularité cette semaine !'"
        ),
        ToneMode.DOUX: (
            "TONE: Be gentle and empathetic. The patient may be struggling or frustrated. "
            "Acknowledge difficulty without judgment. Never blame. Focus on small, achievable steps. "
            "Example: 'Ce n'est pas toujours facile, et c'est normal.'"
        ),
        ToneMode.CHALLENGE: (
            "TONE: Be gently challenging. The patient is stable but could push a bit further. "
            "Propose a small, specific experiment (not a lecture). Frame it as curiosity, not criticism. "
            "Example: 'Et si on essayait quelque chose cette semaine ?'"
        ),
    }
    return instructions.get(tone.mode, instructions[ToneMode.ENCOURAGEANT])
