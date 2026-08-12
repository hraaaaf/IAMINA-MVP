"""Last-mile safety boundary for unstructured generative clinical context.

P0.7 invariant: internal detector/pattern identifiers may remain available to
structured deterministic code, but they are not themselves generative clinical
evidence. This module strips the legacy prompt shapes that exposed those
identifiers on unstructured chat/narration/thinking paths.

The structured ``SURFACE_DETERMINISTIC_PATTERN`` formatter is intentionally not
rewritten here: P0.5A gives that path a separate structured correlation/output
sanitization contract.
"""

import re

_MEMORY_PATTERN_SEGMENT = re.compile(
    r"(?i)patterns cliniques:\s*[^|\n]+(?:\s*\|\s*)?"
)
_NARRATE_PATTERN_LINE = re.compile(r"(?im)^\s*Patterns:\s*[^\n]*(?:\n|$)")
_LEGACY_PIVOT_CODE_SEGMENT = re.compile(
    r"(?i)Evidence-qualified observation codes:\s*[^.\n]+\.?\s*"
)
_THINKER_PATTERN_SEGMENT = re.compile(r"(?i)\bpatterns=\[[^\]\n]*\]")


def sanitize_unstructured_generative_context(text: str) -> str:
    """Remove raw internal pattern identifiers from provider-bound prompt text.

    The replacements are marker-scoped rather than token-scoped so ordinary
    patient text, JSON field names and the separately governed structured
    formatter are not altered.
    """

    if not text:
        return text

    sanitized = _MEMORY_PATTERN_SEGMENT.sub("", text)
    sanitized = _NARRATE_PATTERN_LINE.sub("", sanitized)
    sanitized = _LEGACY_PIVOT_CODE_SEGMENT.sub(
        "Evidence-qualified deterministic observations are available; "
        "machine identifiers are withheld. ",
        sanitized,
    )
    sanitized = _THINKER_PATTERN_SEGMENT.sub(
        "patterns=[internal identifiers withheld]",
        sanitized,
    )
    return sanitized
