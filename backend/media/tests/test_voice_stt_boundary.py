import pytest

from media.voice import MAX_AUDIO_BYTES, transcribe


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
