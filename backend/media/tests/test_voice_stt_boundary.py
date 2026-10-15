from unittest.mock import patch

import pytest

from media.voice import (
    MAX_AUDIO_BYTES,
    GeminiSTTBackend,
    TranscriptionError,
    transcribe,
)


class FakeSTTBackend:
    name = "fake-stt"

    def __init__(self) -> None:
        self.calls = []

    def transcribe(
        self,
        audio_bytes,
        mime_type,
        *,
        language,
        language_hint,
    ):
        self.calls.append(
            {
                "audio_bytes": audio_bytes,
                "mime_type": mime_type,
                "language": language,
                "language_hint": language_hint,
            }
        )
        return "  glycémie cinquante-quatre  "


def test_transcribe_can_use_injected_backend_without_provider_cutover():
    backend = FakeSTTBackend()

    result = transcribe(
        b"synthetic-audio",
        "audio/mp4",
        "fr",
        backend=backend,
    )

    assert result == "glycémie cinquante-quatre"
    assert backend.calls == [
        {
            "audio_bytes": b"synthetic-audio",
            "mime_type": "audio/mp4",
            "language": "fr",
            "language_hint": "French",
        }
    ]


def test_caller_darija_hint_is_forwarded_to_backend():
    backend = FakeSTTBackend()

    transcribe(
        b"synthetic-audio",
        "audio/webm",
        "ar-MA",
        language_hints={"ar-MA": "Moroccan Darija medical vocabulary"},
        backend=backend,
    )

    assert backend.calls[0]["language_hint"] == "Moroccan Darija medical vocabulary"


def test_validation_blocks_bad_mime_before_backend_invocation():
    backend = FakeSTTBackend()

    with pytest.raises(ValueError, match="Unsupported audio format"):
        transcribe(b"audio", "audio/unsafe", backend=backend)

    assert backend.calls == []


def test_validation_blocks_oversize_audio_before_backend_invocation():
    backend = FakeSTTBackend()

    with pytest.raises(ValueError, match="Audio too large"):
        transcribe(b"x" * (MAX_AUDIO_BYTES + 1), "audio/mp4", backend=backend)

    assert backend.calls == []


def test_gemini_unexpected_provider_error_never_logs_sensitive_details():
    canary = "synthetic_private_provider_error_including_patient_data"
    with (
        patch.dict("os.environ", {"GEMINI_API_KEY": "synthetic-test-key"}),
        patch("google.genai.Client"),
        patch(
            "media.voice.execute_external_provider_call",
            side_effect=RuntimeError(canary),
        ),
        patch("media.voice.logger.error") as logged_event,
    ):
        with pytest.raises(TranscriptionError, match="could not be completed safely"):
            GeminiSTTBackend().transcribe(
                b"synthetic-audio",
                "audio/mp4",
                language="fr",
                language_hint="French",
            )

    logged_event.assert_called_once()
    assert "RuntimeError" in str(logged_event.call_args)
    assert canary not in str(logged_event.call_args)
