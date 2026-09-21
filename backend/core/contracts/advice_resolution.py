"""Resolved patient-facing advice produced by a deterministic domain engine."""
from __future__ import annotations

from dataclasses import dataclass

from core.contracts.advice_decision import AdviceDecision, AdviceDisposition


@dataclass(frozen=True, slots=True)
class AdviceResolution:
    """A deterministic decision plus its already-authorized patient-facing copy."""

    decision: AdviceDecision
    reply: str

    def __post_init__(self) -> None:
        if not isinstance(self.decision, AdviceDecision):
            raise ValueError("decision must be an AdviceDecision")
        if not isinstance(self.reply, str) or not self.reply.strip():
            raise ValueError("reply is required")
        object.__setattr__(self, "reply", self.reply.strip())
        if self.decision.decision not in {
            AdviceDisposition.ALLOW,
            AdviceDisposition.CONSTRAIN,
            AdviceDisposition.REFUSE,
            AdviceDisposition.ESCALATE,
        }:
            raise ValueError("unsupported advice disposition")


__all__ = ["AdviceResolution"]
