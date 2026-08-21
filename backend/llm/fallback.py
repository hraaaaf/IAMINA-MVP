import logging

from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class FallbackProvider(BaseLLMProvider):
    """Graceful degraded provider when AI services are offline."""

    def complete(self, system: str, user: str) -> LLMResponse:
        logger.info("FallbackProvider: Serving degraded response.")
        if "summary" in system.lower() or "insight" in system.lower():
            text = (
                "⚠️ Données en cours d'analyse\n"
                "Explication: Vos données glycémiques sont bien enregistrées, mais l'analyse IA détaillée "
                "est momentanément indisponible.\n"
                "Action: Continuez à noter vos glycémies et repas ; je reviendrai vers vous dès que possible."
            )
        else:
            text = (
                "Je suis IAmina, votre assistante. Je rencontre actuellement une petite difficulté technique "
                "pour analyser vos données en profondeur. N'hésitez pas à poser vos questions à votre médecin "
                "ou à réessayer dans quelques minutes."
            )
        return LLMResponse(content=text, provider="fallback-v1")


class QuotaExhaustedProvider(BaseLLMProvider):
    """
    Local deterministic provider returned when the Gemini free-tier daily quota
    is exhausted. The factory intentionally avoids implicit network fallback;
    another network provider must be selected explicitly and remains governed
    by the central processor policy before any egress.
    """

    _CHAT_MSG = (
        "Tu as atteint le quota journalier gratuit d'IAmina ✨\n"
        "Le service reprendra automatiquement demain. "
        "Pour un accès illimité et des analyses en temps réel, "
        "passe à la version Premium 🚀"
    )
    _SUMMARY_MSG = (
        "⚠️ Quota journalier atteint\n"
        "L'analyse IA reprend demain. Tes données sont bien enregistrées — "
        "continue à noter tes glycémies. Passe en Premium pour un accès illimité."
    )

    def complete(self, system: str, user: str) -> LLMResponse:
        logger.warning("QuotaExhaustedProvider: daily Gemini cap hit; serving local response.")
        is_summary = "summary" in system.lower() or "insight" in system.lower()
        return LLMResponse(
            content=self._SUMMARY_MSG if is_summary else self._CHAT_MSG,
            provider="quota-exhausted",
        )

    def stream(self, system: str, user: str):
        msg = self.complete(system, user).content
        words = msg.split(" ")
        for i, word in enumerate(words):
            yield word if i == 0 else " " + word
