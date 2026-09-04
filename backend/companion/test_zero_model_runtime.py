from types import SimpleNamespace
from unittest.mock import patch

from companion.conversation import chat, stream_chat


class ExplodingLLM:
    def complete(self, *_args, **_kwargs):
        raise AssertionError("LLM must not be called for exact zero-model turns")

    def stream(self, *_args, **_kwargs):
        raise AssertionError("LLM stream must not be called for exact zero-model turns")


class BufferedLLM:
    def __init__(self):
        self.complete_calls = 0
        self.stream_calls = 0

    def complete(self, *_args, **_kwargs):
        self.complete_calls += 1
        return SimpleNamespace(content="Réponse brute non validée.")

    def stream(self, *_args, **_kwargs):
        self.stream_calls += 1
        yield "FUITE AVANT GUARD"


def test_exact_greeting_bypasses_llm_in_chat():
    reply = chat("Salut", memory=None, deep=object(), llm=ExplodingLLM())
    assert "Bonjour" in reply


def test_exact_thanks_bypasses_llm_in_stream_chat():
    chunks = list(
        stream_chat("merci", memory=None, deep=object(), llm=ExplodingLLM())
    )
    assert chunks == ["Avec plaisir 🙏"]


def test_exact_farewell_bypasses_llm_in_chat():
    reply = chat("Au revoir", memory=None, deep=object(), llm=ExplodingLLM())
    assert reply == "À bientôt 👋"


def test_bounded_practical_turn_bypasses_llm_in_chat():
    reply = chat(
        "Hier encore j'ai oublié. Je voudrais quelque chose de simple "
        "que je puisse vraiment tenir.",
        memory=None,
        deep=object(),
        llm=ExplodingLLM(),
    )
    assert "Réduis au minimum" in reply


def test_latin_darija_practical_turn_bypasses_llm_in_stream_chat():
    chunks = list(
        stream_chat(
            "Wakha, bghit ghir chi routine sahla bach nb9a mntadem "
            "bla nasi7a 3ilajiya.",
            memory=None,
            deep=object(),
            llm=ExplodingLLM(),
        )
    )
    assert len(chunks) == 1
    assert "3 cases khawyin" in chunks[0]
    assert "reminder" not in chunks[0].lower()


def test_llm_stream_path_buffers_and_guards_before_emission():
    llm = BufferedLLM()
    ctx = SimpleNamespace(pivot_text="approved")

    with (
        patch(
            "companion.conversation._build_runtime_prompt",
            return_value=("fr", ctx, "system", "user"),
        ),
        patch(
            "companion.conversation._finalize_reply",
            return_value="Réponse gardée.",
        ) as finalize,
        patch("companion.conversation.record_companion_route"),
    ):
        chunks = list(
            stream_chat(
                "Peux-tu m'aider à comprendre cette situation ?",
                memory=None,
                deep=object(),
                llm=llm,
            )
        )

    assert chunks == ["Réponse gardée."]
    assert llm.complete_calls == 1
    assert llm.stream_calls == 0
    finalize.assert_called_once()
