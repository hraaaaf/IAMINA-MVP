"""
IAmina Internal State
======================
Pure Python, O(1), zero LLM calls.
Computes IAmina's emotional/clinical state from memory + session context.
This state drives prompt injection (via state_to_prompt) but is NEVER shown to the patient.
"""
from dataclasses import dataclass
from datetime import date

from companion.deep_memory import IAminaDeepMemory
from companion.memory import IAminaMemory
from core.contracts.domain_context import DomainContext


@dataclass
class IAminaState:
    satisfaction: float      # 0.0–1.0
    concern_level: float     # 0.0–1.0
    engagement: float        # 0.0–1.0
    clinical_mood: str       # "optimistic"|"watchful"|"concerned"|"alarmed"
    next_intention: str      # short phrase describing what IAmina intends to do
    self_note: str           # internal thought about the patient (French, ~1 sentence, not shown to patient)


def compute_state(
    memory: IAminaMemory,
    deep: IAminaDeepMemory,
    ctx: DomainContext,
) -> IAminaState:
    """
    Compute IAmina's internal state from memory, deep memory, and session context.
    Pure Python — no LLM calls, no ORM queries, O(1).

    `tir`/`cv` below are the generic primary/stability tone signals. Thresholds
    (70/55/40/36) are TIR-calibrated; per-module calibration is a P7 concern.
    """
    tir = ctx.tone_signals.get("primary")     # float | None — primary score (diabetes: TIR%)
    cv = ctx.tone_signals.get("stability")    # float | None — stability (diabetes: CV%)
    tir_trend = ctx.trend or {}
    trend_direction = tir_trend.get("direction", "unknown")

    # ── satisfaction ──────────────────────────────────────────────────────────
    satisfaction = 0.0
    if tir is not None:
        if tir >= 70:
            satisfaction += 0.5
        elif tir >= 50:
            satisfaction += 0.3
        else:
            satisfaction += 0.1

    if deep.consecutive_log_days >= 7:
        satisfaction += 0.2
    elif deep.consecutive_log_days >= 3:
        satisfaction += 0.1

    if memory.milestones_celebrated:
        satisfaction += 0.1

    satisfaction = min(satisfaction, 1.0)

    # ── concern_level ─────────────────────────────────────────────────────────
    concern_level = 0.0
    if tir is not None:
        if tir < 40:
            concern_level += 0.5
        elif tir < 55:
            concern_level += 0.3

    if cv is not None and cv > 36:
        concern_level += 0.2

    if trend_direction == "down":
        concern_level += 0.2

    emotional = memory.emotional_signals or []
    if "discouragement" in emotional or "fear" in emotional:
        concern_level += 0.2

    # last_log_date > 3 days ago AND consecutive_log_days == 0
    if deep.consecutive_log_days == 0 and deep.last_log_date:
        try:
            last = date.fromisoformat(deep.last_log_date)
            days_since = (date.today() - last).days
            if days_since > 3:
                concern_level += 0.1
        except (ValueError, TypeError):
            pass

    concern_level = min(concern_level, 1.0)

    # ── engagement ────────────────────────────────────────────────────────────
    engagement = 0.0
    engagement += min(deep.total_interactions / 50, 0.6)

    stage_bonus = {
        "new": 0.0,
        "building": 0.1,
        "trusted": 0.2,
        "companion": 0.3,
    }
    engagement += stage_bonus.get(deep.relationship_stage, 0.0)

    if deep.consecutive_log_days >= 5:
        engagement += 0.1

    engagement = min(engagement, 1.0)

    # ── clinical_mood ─────────────────────────────────────────────────────────
    if concern_level > 0.6:
        clinical_mood = "alarmed"
    elif concern_level > 0.35:
        clinical_mood = "concerned"
    elif satisfaction > 0.6:
        clinical_mood = "optimistic"
    else:
        clinical_mood = "watchful"

    # ── next_intention ────────────────────────────────────────────────────────
    if memory.milestones_celebrated:
        last_milestone = memory.milestones_celebrated[-1]
        next_intention = f"célébrer le jalon {last_milestone}"
    elif concern_level > 0.5 and trend_direction == "down":
        next_intention = "mentionner doucement la tendance à la baisse"
    elif deep.consecutive_log_days >= 7:
        next_intention = "souligner la régularité et encourager"
    elif emotional:
        next_intention = "commencer par prendre des nouvelles"
    else:
        next_intention = "écouter et accompagner"

    # ── self_note ─────────────────────────────────────────────────────────────
    tir_str = f"{ctx.primary_label} {tir:.0f}%" if tir is not None else "données insuffisantes"
    streak_str = f"streak {deep.consecutive_log_days}j" if deep.consecutive_log_days > 0 else "pas de streak actif"
    style = deep.communication_style or "unknown"

    trend_note = ""
    if trend_direction == "down":
        trend_note = ", tendance baissière"
    elif trend_direction == "up":
        trend_note = ", tendance en hausse"

    style_note = ""
    if style == "data_driven":
        style_note = " — aime les chiffres, rester factuel"
    elif style in ("unknown", ""):
        style_note = " — style inconnu, rester chaleureux et observer"
    else:
        style_note = f" — style {style}"

    self_note = (
        f"Patient ({tir_str}{trend_note}), {streak_str}{style_note}."
    )

    return IAminaState(
        satisfaction=satisfaction,
        concern_level=concern_level,
        engagement=engagement,
        clinical_mood=clinical_mood,
        next_intention=next_intention,
        self_note=self_note,
    )


def state_to_prompt(state: IAminaState) -> str:
    """
    Format IAminaState for injection into the system prompt.
    This block is appended to SYSTEM_BASE via SYSTEM_WITH_STATE.
    """
    return (
        f"[ÉTAT INTERNE IAMINA]\n"
        f"Satisfaction: {state.satisfaction:.2f} | "
        f"Inquiétude: {state.concern_level:.2f} | "
        f"Engagement: {state.engagement:.2f}\n"
        f"Humeur clinique: {state.clinical_mood}\n"
        f"Prochaine intention: {state.next_intention}\n"
        f"Note interne: {state.self_note}"
    )
