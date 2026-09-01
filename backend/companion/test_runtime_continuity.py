from types import SimpleNamespace

import pytest

from companion import conversation


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Résume ce qu'on vient de décider en une phrase simple.", "recap"),
        ("Summarize what we just decided in one simple sentence.", "recap"),
        ("لخّص ما اتفقنا عليه الآن في جملة بسيطة واحدة.", "recap"),
        ("وش اتفقنا عليه الحين بجملة بسيطة وحدة؟", "recap"),
        ("شنو اتفقنا عليه دابا فجملة وحدة؟", "recap"),
    ],
)
def test_response_mode_detects_recap_across_supported_language_families(message, expected):
    assert conversation._response_mode(message) == expected


def test_verbatim_repeat_detection_is_whitespace_and_case_insensitive(monkeypatch):
    monkeypatch.setattr(
        conversation,
        "_recent_turns",
        lambda *args, **kwargs: [SimpleNamespace(message="Start with one anchor.")],
    )

    assert conversation._is_verbatim_repeat(
        "  start   with one ANCHOR. ",
        patient=object(),
        mode="practical",
    )


def test_emotional_reply_never_triggers_continuity_retry(monkeypatch):
    monkeypatch.setattr(
        conversation,
        "_recent_turns",
        lambda *args, **kwargs: [SimpleNamespace(message="Same empathy")],
    )

    assert not conversation._is_verbatim_repeat(
        "Same empathy",
        patient=object(),
        mode="emotional",
    )


def test_recap_retry_requires_history_synthesis_not_previous_reply_recycling():
    prompt = conversation._continuity_retry_prompt("base", "recap")

    assert "tout ce qui a été convenu dans l'historique" in prompt
    assert "sans recycler une réponse précédente" in prompt
    assert "n'invente aucune action santé/comportementale" in prompt
