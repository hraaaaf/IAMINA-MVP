"""V1-03 strict external *text* contract: generic immutable prompts only.

Regex anonymization is not proof that patient facts or context are absent.
Nothing derived from patient messages, clinical logs, histories, state, locale,
or a dynamic model-generated draft may cross this boundary.

The exact pair below is a non-personal certification fixture. It has no patient
content and provides no clinical functionality. Patient-generative text stays
local until separately reviewed opaque-token-only transport is implemented.
"""
from __future__ import annotations

from core.ai_processor_policy import AIProcessorPolicyDenied

# Static, intentionally non-personal and NOT composed from request fields.
GENERIC_SYSTEM_PROMPT = (
    "Repeat the fixed greeting exactly. Do not add facts or suggestions."
)
GENERIC_USER_PROMPT = "Hello."


def assert_v1_external_text_generic_only(system_prompt: str, user_prompt: str) -> None:
    """Reject all dynamic or patient-derived text before an external provider call."""
    if (system_prompt, user_prompt) != (GENERIC_SYSTEM_PROMPT, GENERIC_USER_PROMPT):
        raise AIProcessorPolicyDenied(
            "V1-03 external text requires a preapproved static generic payload; "
            "patient-context narration must remain local"
        )
