import logging
import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import Iterator

from google import genai

from .base import BaseLLMProvider, LLMResponse, LLMUsage

logger = logging.getLogger(__name__)

_LLM_TIMEOUT = 15  # seconds


def _usage_from_response(response) -> LLMUsage | None:
    metadata = getattr(response, "usage_metadata", None)
    if metadata is None:
        return None

    def _value(name: str) -> int | None:
        raw = getattr(metadata, name, None)
        return int(raw) if raw is not None else None

    return LLMUsage(
        input_tokens=_value("prompt_token_count"),
        output_tokens=_value("candidates_token_count"),
        cached_input_tokens=_value("cached_content_token_count"),
        total_tokens=_value("total_token_count"),
    )


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider (gemini-2.5-flash by default).

    Note: gemini-2.5-flash follows JSON schemas significantly more reliably
    than gemini-2.5-flash-lite. Use flash-lite only for non-structured output.
    """

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GeminiProvider: No API key found. Calls will fail.")
        self._client = (
            genai.Client(
                api_key=api_key,
                http_options={"api_version": "v1alpha"},
            )
            if api_key
            else None
        )
        self._executor = ThreadPoolExecutor(max_workers=1)

    @property
    def model_name(self) -> str:
        return self.model

    def _call_with_timeout(self, fn):
        future = self._executor.submit(fn)
        try:
            return future.result(timeout=_LLM_TIMEOUT)
        except FuturesTimeoutError:
            future.cancel()
            raise TimeoutError(f"Gemini API call timed out after {_LLM_TIMEOUT}s") from None

    def complete(self, system: str, user: str) -> LLMResponse:
        if not self._client:
            raise RuntimeError("GeminiProvider: client not initialized (missing API key).")

        def _do_complete():
            return self._client.models.generate_content(
                model=self.model,
                contents=user,
                config={
                    "system_instruction": system,
                    "temperature": 0.1,
                },
            )

        response = self._call_with_timeout(_do_complete)
        return LLMResponse(
            content=response.text.strip() if response.text else "",
            provider=self.model,
            usage=_usage_from_response(response),
        )

    def stream(self, system: str, user: str) -> Iterator[str]:
        """Yield Gemini chunks after one bounded provider operation."""
        if not self._client:
            raise RuntimeError("GeminiProvider: client not initialized (missing API key).")

        def _do_stream():
            return list(
                self._client.models.generate_content_stream(
                    model=self.model,
                    contents=user,
                    config={
                        "system_instruction": system,
                        "temperature": 0.1,
                    },
                )
            )

        chunks = self._call_with_timeout(_do_stream)
        for chunk in chunks:
            if chunk.text:
                yield chunk.text

    def think(self, system: str, user: str) -> tuple[str, str]:
        """Run Gemini thinking through the same bounded execution path."""
        if not self._client:
            return "", ""

        def _do_think():
            return self._client.models.generate_content(
                model=self.model,
                contents=user,
                config={
                    "system_instruction": system,
                    "thinking_config": {"thinking_budget": 2048},
                    "temperature": 1.0,
                },
            )

        try:
            response = self._call_with_timeout(_do_think)
            thinking = ""
            text = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, "thought") and part.thought:
                    thinking += part.text
                else:
                    text += part.text
            logger.debug(
                "GeminiProvider.think: thinking_tokens=%d",
                len(thinking.split()),
            )
            return thinking.strip(), text.strip()
        except TimeoutError:
            raise
        except Exception:
            logger.debug(
                "GeminiProvider.think: thinking unavailable, falling back to complete()"
            )
            result = self.complete(system, user)
            return "", result.content
