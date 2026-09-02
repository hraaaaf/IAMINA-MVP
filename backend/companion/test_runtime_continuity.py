from types import SimpleNamespace

import pytest

from companion import conversation, narrator_prompts


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


def test_recap_rejects_repeat_of_older_assistant_turn(monkeypatch):
    calls = []

    def recent_turns(_patient, limit, role=None, **_kwargs):
        calls.append((limit, role))
        return [
            SimpleNamespace(message="Prepare these four questions."),
            SimpleNamespace(message="Start with one anchor."),
            SimpleNamespace(message="Strip it down."),
        ][:limit]

    monkeypatch.setattr(conversation, "_recent_turns", recent_turns)

    assert conversation._is_verbatim_repeat(
        "Start with one anchor.",
        patient=object(),
        mode="recap",
    )
    assert calls[-1] == (20, "assistant")


def test_practical_repeat_only_compares_latest_assistant_turn(monkeypatch):
    calls = []

    def recent_turns(_patient, limit, role=None, **_kwargs):
        calls.append((limit, role))
        return [
            SimpleNamespace(message="Prepare these four questions."),
            SimpleNamespace(message="Start with one anchor."),
        ][:limit]

    monkeypatch.setattr(conversation, "_recent_turns", recent_turns)

    assert not conversation._is_verbatim_repeat(
        "Start with one anchor.",
        patient=object(),
        mode="practical",
    )
    assert calls[-1] == (1, "assistant")


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


def test_narrator_contract_requires_direct_practical_help_before_questions():
    assert "Ne réponds jamais uniquement par des questions de clarification" in narrator_prompts.SYSTEM_WITH_STATE
    assert "ne réponds jamais uniquement par des questions" in narrator_prompts.CHAT_USER


def test_narrator_contract_recap_must_cover_more_than_latest_exchange():
    assert "au moins deux éléments distincts" in narrator_prompts.SYSTEM_WITH_STATE
    assert "un résumé du seul dernier échange est invalide" in narrator_prompts.CHAT_USER
