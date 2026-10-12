"""V1-03: policy-denied cloud media preserves safe manual input paths."""
from __future__ import annotations

import base64
from types import SimpleNamespace

import pytest

from ai.api.v1 import ai as ai_routes
from ai.api.v1 import voice as voice_routes
from core.ai_egress import AIEgressDenied
from core.ai_processor_policy import AIProcessorPolicyDenied


@pytest.fixture
def fake_request():
    return SimpleNamespace(user=SimpleNamespace(id=41))


@pytest.fixture
def image_request():
    return ai_routes.MealImageRequest(
        image_base64=base64.b64encode(b"synthetic-image").decode("ascii"),
        mime_type="image/jpeg",
    )


@pytest.mark.parametrize(
    ("route", "backend", "expected"),
    [
        (
            ai_routes.analyze_meal_image,
            "analyze_meal_image",
            {"foods": [], "confidence": "low", "fallback": True},
        ),
        (
            ai_routes.analyze_glucometer_image_web,
            "analyze_glucometer_image",
            {"value": None, "unit": "mg/dL", "confidence": "low", "fallback": True},
        ),
    ],
)
def test_denied_vision_returns_manual_fallback(
    fake_request, image_request, monkeypatch, route, backend, expected
):
    calls = []

    def denied(*args):
        calls.append("attempt")
        raise AIProcessorPolicyDenied("synthetic blocked provider")

    monkeypatch.setattr(f"media.vision.{backend}", denied)
    assert route(fake_request, image_request) == expected
    assert calls == ["attempt"]


@pytest.mark.parametrize(
    ("route", "backend"),
    [
        (ai_routes.analyze_meal_image, "analyze_meal_image"),
        (ai_routes.analyze_glucometer_image_web, "analyze_glucometer_image"),
    ],
)
def test_missing_consent_is_not_misreported_as_successful_fallback(
    fake_request, image_request, monkeypatch, route, backend
):
    def denied(*args):
        raise AIEgressDenied("consent missing")

    monkeypatch.setattr(f"media.vision.{backend}", denied)
    with pytest.raises(AIEgressDenied, match="consent missing"):
        route(fake_request, image_request)


@pytest.mark.parametrize("route", ["voice_chat", "transcribe_audio"])
def test_denied_voice_returns_safely_without_transcript_or_chat(
    fake_request, monkeypatch, route
):
    monkeypatch.setattr("ai.api.v1.voice._get_language", lambda user: "fr")
    calls = []

    def blocked_transcriber(*args, **kwargs):
        calls.append("transcribe")
        raise AIProcessorPolicyDenied("synthetic blocked provider")

    monkeypatch.setattr("ai.api.v1.voice.transcribe", blocked_transcriber)
    audio = SimpleNamespace(content_type="audio/mp4", read=lambda: b"synthetic-audio")
    result = getattr(voice_routes, route)(fake_request, audio)
    assert calls == ["transcribe"]
    if route == "voice_chat":
        assert result["transcript"] == ""
        assert result["reply"]
        assert result["is_emergency"] is False
    else:
        assert result == {"transcript": "", "confidence": "low"}


def test_voice_consent_denial_is_not_swallowed(fake_request, monkeypatch):
    monkeypatch.setattr("ai.api.v1.voice._get_language", lambda user: "fr")

    def denied(*args, **kwargs):
        raise AIEgressDenied("consent missing")

    monkeypatch.setattr("ai.api.v1.voice.transcribe", denied)
    audio = SimpleNamespace(content_type="audio/mp4", read=lambda: b"synthetic-audio")
    with pytest.raises(AIEgressDenied, match="consent missing"):
        voice_routes.voice_chat(fake_request, audio)
