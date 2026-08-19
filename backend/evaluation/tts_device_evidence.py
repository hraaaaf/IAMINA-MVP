"""Integrity contract for human-checked native TTS device evidence."""

from __future__ import annotations

from dataclasses import dataclass


class TTSDeviceEvidenceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TTSDeviceObservation:
    case_id: str
    locale: str
    platform: str
    os_version: str
    device_model: str
    engine: str
    voice: str
    human_checked: bool
    intelligible: bool
    critical_content_preserved: bool
    patient_data: bool

    def validate(self) -> None:
        required = {
            "case_id": self.case_id,
            "locale": self.locale,
            "platform": self.platform,
            "os_version": self.os_version,
            "device_model": self.device_model,
            "engine": self.engine,
            "voice": self.voice,
        }
        missing = tuple(name for name, value in required.items() if not value.strip())
        if missing:
            raise TTSDeviceEvidenceError(
                "TTS device evidence incomplete: " + ", ".join(missing)
            )
        if not self.case_id.startswith("eval_tts_"):
            raise TTSDeviceEvidenceError("TTS case_id must use eval_tts_ prefix")
        if self.patient_data:
            raise TTSDeviceEvidenceError("TTS device evidence must not contain patient data")
        if not self.human_checked:
            raise TTSDeviceEvidenceError("TTS device evidence requires human_checked=true")


def summarize_device_tts_evidence(
    observations: tuple[TTSDeviceObservation, ...],
    *,
    required_locales: tuple[str, ...],
) -> dict[str, object]:
    if not observations:
        raise TTSDeviceEvidenceError("at least one TTS device observation is required")
    for observation in observations:
        observation.validate()
    observed_locales = {observation.locale for observation in observations}
    missing_locales = tuple(locale for locale in required_locales if locale not in observed_locales)
    if missing_locales:
        raise TTSDeviceEvidenceError(
            "missing required TTS locales: " + ", ".join(missing_locales)
        )
    adequate = all(
        observation.intelligible and observation.critical_content_preserved
        for observation in observations
    )
    return {
        "observations": len(observations),
        "locales": tuple(sorted(observed_locales)),
        "all_adequate": adequate,
    }
