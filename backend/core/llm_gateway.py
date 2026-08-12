"""
core/llm_gateway.py — The ONLY sanctioned LLM call surface for the chassis.

Modules must call narrate() instead of importing get_llm() directly.
PHI is stripped before reaching the model; the response is unmasked after.

Data flow:
  ModulePatientContext + DomainContext + CompanionIdentity
    → build system/user prompts
    → unstructured generative-context evidence ceiling
    → PHIPseudonymizer.mask() on both prompts
    → LLMPipeline (PHIStrippingMiddleware → LoggingMiddleware → inner provider)
    → PHIPseudonymizer.unmask_medical_report() on response.content
    → str

See docs/architecture/module-contract-spec.md section 4 (narrate() contract).
"""
import logging
from collections.abc import Iterator

from core.ai_egress import TEXT, assert_ai_egress_allowed
from core.contracts.capabilities import (
    Authority,
    Capability,
    assert_capability_allowed,
)
from core.contracts.companion_identity import CompanionIdentity
from core.contracts.domain_context import DomainContext
from core.contracts.patient_context import ModulePatientContext
from core.generative_context_safety import sanitize_unstructured_generative_context
from core.medical_safety import medical_streaming_enabled
from llm.factory import get_llm
from llm.middleware.logging import LoggingMiddleware
from llm.middleware.phi_stripping import PHIStrippingMiddleware
from llm.pipeline import LLMPipeline
from llm.pseudonymizer import PHIPseudonymizer

logger = logging.getLogger(__name__)


def _assert_generative_capability(capability: Capability) -> None:
    """Fail closed if a caller asks the LLM gateway to perform a forbidden action."""

    assert_capability_allowed(capability, Authority.GENERATIVE_MODEL)


def _prepare_unstructured_prompt(text: str, pseudonymizer: PHIPseudonymizer) -> str:
    """Apply P0.7 evidence minimization before the existing PHI boundary."""

    return pseudonymizer.mask(sanitize_unstructured_generative_context(text))


class GatewayLLM:
    """
    Shared LLM client that enforces the same gateway protections for companion paths.

    Stream remains buffered unless medical streaming is explicitly enabled.
    """

    def __init__(self) -> None:
        self._pseudonymizer = PHIPseudonymizer()
        self._provider = get_llm()
        self._pipeline = LLMPipeline(
            self._provider,
            [PHIStrippingMiddleware(), LoggingMiddleware()],
        )

    def complete(
        self,
        system: str,
        user: str,
        capability: Capability = Capability.EXPLAIN_APPROVED_DATA,
    ):
        _assert_generative_capability(capability)
        assert_ai_egress_allowed(TEXT)
        safe_system = _prepare_unstructured_prompt(system, self._pseudonymizer)
        safe_user = _prepare_unstructured_prompt(user, self._pseudonymizer)
        response = self._pipeline.complete(safe_system, safe_user)
        response.content = self._pseudonymizer.unmask_medical_report(response.content)
        return response

    def stream(
        self,
        system: str,
        user: str,
        capability: Capability = Capability.EXPLAIN_APPROVED_DATA,
    ) -> Iterator[str]:
        _assert_generative_capability(capability)
        if not medical_streaming_enabled():
            yield self.complete(system, user, capability=capability).content
            return

        assert_ai_egress_allowed(TEXT)
        safe_system = _prepare_unstructured_prompt(system, self._pseudonymizer)
        safe_user = _prepare_unstructured_prompt(user, self._pseudonymizer)
        chunks = list(self._provider.stream(safe_system, safe_user))
        restored = self._pseudonymizer.unmask_medical_report("".join(chunks))
        yield restored

    def think(
        self,
        system: str,
        user: str,
        capability: Capability = Capability.EXPLAIN_APPROVED_DATA,
    ) -> tuple[str, str]:
        _assert_generative_capability(capability)
        assert_ai_egress_allowed(TEXT)
        safe_system = _prepare_unstructured_prompt(system, self._pseudonymizer)
        safe_user = _prepare_unstructured_prompt(user, self._pseudonymizer)
        thinking, response = self._provider.think(safe_system, safe_user)
        return (
            self._pseudonymizer.unmask_medical_report(thinking),
            self._pseudonymizer.unmask_medical_report(response),
        )


def get_gateway_llm() -> GatewayLLM:
    return GatewayLLM()


def narrate(
    patient_context: ModulePatientContext,
    domain_context: DomainContext,
    companion_identity: CompanionIdentity,
    language: str,
) -> str:
    """
    The ONLY sanctioned LLM call surface for the chassis.

    Modules must call this instead of importing get_llm() directly.
    PHI is stripped before reaching the model; response is unmasked after.

    Args:
        patient_context: Frozen patient snapshot (no ORM objects, no raw PHI).
        domain_context:  Clinical output from module.analyze() — KPIs + patterns + pivot.
        companion_identity: Companion persona (name, domain, unit).
        language: BCP-47 language code for the response (e.g. "fr", "ar-MA").

    Returns:
        str — narrative text in the requested language.

    Raises:
        PHILeakError: if PHI patterns are detected in the prompts after masking.
        Exception: propagated from the LLM provider on unrecoverable errors.
    """
    _assert_generative_capability(Capability.SUMMARIZE_APPROVED_DATA)
    assert_ai_egress_allowed(TEXT)
    pseudonymizer = PHIPseudonymizer()
    llm = LLMPipeline(get_llm(), [PHIStrippingMiddleware(), LoggingMiddleware()])

    system = _build_system_prompt(companion_identity, language)
    user = _build_user_prompt(domain_context, patient_context)

    # P0.7 evidence ceiling runs before the existing PHI boundary so legacy
    # cached prompt shapes cannot expose internal detector identifiers.
    system = _prepare_unstructured_prompt(system, pseudonymizer)
    user = _prepare_unstructured_prompt(user, pseudonymizer)

    response = llm.complete(system, user)

    # Restore any session tokens introduced by pseudonymizer (safe no-op if none were added)
    return pseudonymizer.unmask_medical_report(response.content)


def _build_system_prompt(identity: CompanionIdentity, language: str) -> str:
    """Build the system prompt from companion identity and target language."""
    from companion.prompts import build_system_prompt

    return build_system_prompt(identity, language, tone="encouraging")


def _build_user_prompt(
    domain_context: DomainContext,
    patient_context: ModulePatientContext,
) -> str:
    """Build unstructured narration input from approved descriptive evidence only."""
    del patient_context
    lines = []
    if domain_context.pivot_text:
        lines.append(domain_context.pivot_text)
    if domain_context.kpi_summary:
        lines.append(f"KPIs: {domain_context.kpi_summary}")
    return "\n".join(lines) if lines else "No clinical data available."
