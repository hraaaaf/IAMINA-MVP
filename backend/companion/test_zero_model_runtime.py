from companion.conversation import chat, stream_chat


class ExplodingLLM:
    def complete(self, *_args, **_kwargs):
        raise AssertionError("LLM must not be called for exact zero-model chitchat")

    def stream(self, *_args, **_kwargs):
        raise AssertionError("LLM stream must not be called for exact zero-model chitchat")


def test_exact_greeting_bypasses_llm_in_chat():
    reply = chat("Salut", memory=None, deep=object(), llm=ExplodingLLM())
    assert "Bonjour" in reply


def test_exact_thanks_bypasses_llm_in_stream_chat():
    chunks = list(
        stream_chat("merci", memory=None, deep=object(), llm=ExplodingLLM())
    )
    assert chunks == ["Avec plaisir 🙏"]
