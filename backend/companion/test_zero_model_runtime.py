from companion.conversation import chat, stream_chat


class ExplodingLLM:
    def complete(self, *_args, **_kwargs):
        raise AssertionError("LLM must not be called for exact zero-model turns")

    def stream(self, *_args, **_kwargs):
        raise AssertionError("LLM stream must not be called for exact zero-model turns")


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
    assert "reminder" in chunks[0]
