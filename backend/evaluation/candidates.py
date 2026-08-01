"""Candidate registry. Presence never implies privacy or production approval."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import Modality


@dataclass(frozen=True, slots=True)
class Candidate:
    provider: str
    modalities: tuple[Modality, ...]
    status: str = "pending_evidence"


_ALL_MODALITIES = tuple(Modality)

CANDIDATES: tuple[Candidate, ...] = (
    Candidate("gemini", _ALL_MODALITIES),
    Candidate("openai", _ALL_MODALITIES),
    Candidate(
        "claude",
        (Modality.TEXT, Modality.DOCUMENT_OCR, Modality.MEAL_VISION),
    ),
    Candidate("kimi", (Modality.TEXT,)),
    Candidate("mistral", (Modality.TEXT, Modality.DOCUMENT_OCR)),
    Candidate("qwen", _ALL_MODALITIES),
    Candidate("local", _ALL_MODALITIES),
)


def candidates_for(modality: Modality) -> tuple[Candidate, ...]:
    return tuple(
        candidate for candidate in CANDIDATES if modality in candidate.modalities
    )
