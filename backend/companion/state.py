"""
IAmina Internal State
======================
Pure Python, O(1), zero LLM calls.

P3 contract: this state is relationship/conversation state only. Clinical truth,
priority and longitudinal meaning stay in module-owned DomainContext /
CompanionContext and must never be recreated here.
"""
from dataclasses import dataclass
from datetime import date

from companion.deep_memory import IAminaDeepMemory
from companion.memory import IAminaMemory
from core.contracts.domain_context import DomainContext


@dataclass
class IAminaState:
    satisfaction: float      # relationship/engagement signal, 0.0–1.0
    concern_level: float     # emotional/engagement concern only, 0.0–1.0
    engagement: float        # 0.0–1.0
    clinical_mood: str       # legacy field name; relationship-derived only in P3
    next_intention: str      # conversational intention only
    self_note: str           # relationship note, never clinical truth


def compute_state(
    memory: IAminaMemory,
    deep: IAminaDeepMemory,
    ctx: DomainContext,
) -> IAminaState:
    """Compute relationship state without creating clinical semantics.

    ``ctx`` is retained in the signature for compatibility but deliberately not
    interpreted here. Approved clinical meaning is injected separately from the
    active module contracts.
    """
    del ctx

    satisfaction = 0.0
    if deep.consecutive_log_days >= 7:
        satisfaction += 0.4
    elif deep.consecutive_log_days >= 3:
        satisfaction += 0.2
    if memory.milestones_celebrated:
        satisfaction += 0.2
    if deep.total_interactions >= 10:
        satisfaction += 0.2
    satisfaction = min(satisfaction, 1.0)

    emotional = memory.emotional_signals or []
    concern_level = 0.0
    if "discouragement" in emotional or "fear" in emotional:
        concern_level += 0.4

    if deep.consecutive_log_days == 0 and deep.last_log_date:
        try:
            last = date.fromisoformat(deep.last_log_date)
            days_since = (date.today() - last).days
            if days_since > 3:
                concern_level += 0.1
        except (ValueError, TypeError):
            pass
    concern_level = min(concern_level, 1.0)

    engagement = min(deep.total_interactions / 50, 0.6)
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

    if concern_level > 0.35:
        clinical_mood = "concerned"
    elif satisfaction > 0.6:
        clinical_mood = "optimistic"
    else:
        clinical_mood = "watchful"

    if memory.milestones_celebrated:
        last_milestone = memory.milestones_celebrated[-1]
        next_intention = f"célébrer le jalon {last_milestone}"
    elif emotional:
        next_intention = "répondre avec attention à l'état émotionnel"
    elif deep.consecutive_log_days >= 7:
        next_intention = "souligner la régularité et encourager"
    else:
        next_intention = "écouter et accompagner"

    style = deep.communication_style or "unknown"
    streak_str = (
        f"streak {deep.consecutive_log_days}j"
        if deep.consecutive_log_days > 0
        else "pas de streak actif"
    )
    if style == "data_driven":
        style_note = "aime les explications factuelles"
    elif style in ("unknown", ""):
        style_note = "style encore inconnu"
    else:
        style_note = f"style {style}"
    self_note = f"Relation: {streak_str}, {style_note}."

    return IAminaState(
        satisfaction=satisfaction,
        concern_level=concern_level,
        engagement=engagement,
        clinical_mood=clinical_mood,
        next_intention=next_intention,
        self_note=self_note,
    )


def state_to_prompt(state: IAminaState) -> str:
    """Format relationship state for prompt injection without clinical authority."""
    return (
        f"[ÉTAT RELATIONNEL IAMINA]\n"
        f"Satisfaction: {state.satisfaction:.2f} | "
        f"Attention émotionnelle: {state.concern_level:.2f} | "
        f"Engagement: {state.engagement:.2f}\n"
        f"Tonalité relationnelle: {state.clinical_mood}\n"
        f"Prochaine intention conversationnelle: {state.next_intention}\n"
        f"Note relationnelle: {state.self_note}"
    )
