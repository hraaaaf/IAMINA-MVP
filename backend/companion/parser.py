import json
import logging
import re

logger = logging.getLogger(__name__)

# Keys the LLM sometimes uses instead of the schema-specified key.
# Checked in order; first non-empty value wins.
_REPLY_ALIASES = ("reply", "response", "message", "text", "content", "answer")
_DOCTOR_BRIEF_FIELDS = ("narrative", "key_insight", "doctor_brief")


def strip_fences(content: str) -> str:
    """Extract JSON from LLM output — robust to preamble text and fence variants."""
    s = content.strip()
    # 1. Code fence anywhere in the content (handles preamble text before ```)
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', s)
    if m:
        return m.group(1).strip()
    # 2. No fence — find the first { or [ and take from there
    for i, ch in enumerate(s):
        if ch in ('{', '['):
            return s[i:]
    return s


def parse_llm_json(content: str, fields: list[str]) -> dict:
    """
    DRY: single place for LLM JSON parsing.
    Never crashes — returns empty strings for missing fields.
    Strips markdown fences. Falls back to alias keys for common mismatches.

    The doctor-brief schema has an additional fail-closed epistemic boundary:
    a generated field that asserts unsupported causality/diagnosis/mechanism or
    an unauthorized intervention is discarded instead of being promoted into
    patient/clinician-visible text.
    """
    clean = strip_fences(content)
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON: %s", content[:120])
        data = {}

    result: dict = {}
    for f in fields:
        if f in data:
            result[f] = data[f]
        else:
            # Try aliases only for the main text-content field (first field)
            alias_val = ""
            if f == fields[0]:
                for alias in _REPLY_ALIASES:
                    if alias != f and alias in data and data[alias]:
                        alias_val = data[alias]
                        logger.debug("parse_llm_json: used alias '%s' for field '%s'", alias, f)
                        break
            result[f] = alias_val or ""

    if tuple(fields) == _DOCTOR_BRIEF_FIELDS:
        from core.epistemic_safety import violates_epistemic_claim_policy

        for field in _DOCTOR_BRIEF_FIELDS:
            value = result.get(field)
            if isinstance(value, str) and violates_epistemic_claim_policy(value):
                logger.warning("doctor-brief epistemic overclaim discarded: field=%s", field)
                result[field] = ""

    return result
