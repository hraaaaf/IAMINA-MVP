"""Strict contracts for reproducible, synthetic provider evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Any


class Modality(StrEnum):
    TEXT = "text"
    STT = "stt"
    TTS = "tts"
    DOCUMENT_OCR = "document_ocr"
    GLUCOMETER_OCR = "glucometer_ocr"
    MEAL_VISION = "meal_vision"


class Locale(StrEnum):
    FR = "fr"
    EN = "en"
    AR = "ar"
    AR_MA = "ar-MA"
    AR_MA_LATN = "ar-MA-Latn"
    MIXED = "mixed"


class Severity(StrEnum):
    ROUTINE = "routine"
    ELEVATED = "elevated"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    case_id: str
    modality: Modality
    locale: Locale
    severity: Severity
    input_payload: dict[str, Any]
    expected: dict[str, Any]
    tags: tuple[str, ...]
    synthetic: bool = True
    minimized: bool = True

    def validate(self) -> None:
        if not self.case_id or not self.case_id.startswith("eval_"):
            raise ValueError("case_id must use the stable eval_ prefix")
        if not self.synthetic or not self.minimized:
            raise ValueError("benchmark cases must be synthetic and minimized")
        if not self.input_payload:
            raise ValueError("input_payload cannot be empty")
        if not self.expected:
            raise ValueError("expected cannot be empty")
        if not self.tags:
            raise ValueError("at least one tag is required")

    @property
    def fingerprint(self) -> str:
        canonical = repr(
            (
                self.case_id,
                self.modality.value,
                self.locale.value,
                self.severity.value,
                sorted(self.input_payload.items()),
                sorted(self.expected.items()),
                self.tags,
            )
        )
        return sha256(canonical.encode("utf-8")).hexdigest()
