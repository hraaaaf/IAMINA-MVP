"""Deterministic privacy minimization before any external text-model egress.

This is a defense-in-depth layer, not a legal certification of anonymisation.
It runs after existing prompt sanitisation/pseudonymisation and before the final
DLP + processor-policy authorization boundary.

The gateway deliberately:
- removes stable/direct identifiers missed upstream;
- coarsens precise temporal and age information;
- withholds exact clinical measurements and coordinates;
- removes explicitly-labelled location fields;
- fails closed if a known high-risk pattern survives transformation.

The output is deterministic and contains no reversible mapping.
"""

from __future__ import annotations

import collections.abc
import re
import unicodedata
from dataclasses import dataclass, field
from types import MappingProxyType


_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)


class AnonymizationRiskDenied(PermissionError):
    """Raised when provider-bound text still contains known re-identification risk."""


@dataclass(frozen=True, slots=True)
class AnonymizationResult:
    """Immutable minimized payload plus non-sensitive transformation metadata."""

    fields: collections.abc.Mapping[str, str]
    transformations: tuple[str, ...]
    residual_findings: frozenset[str]
    # Deliberately non-initializable: this layer can never self-certify legal anonymity.
    certified_anonymous: bool = field(init=False, default=False)


_EMAIL = re.compile(
    r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])",
    re.IGNORECASE,
)
_PHONE = re.compile(
    r"(?<!\w)(?:(?:\+|00)\d{1,3}(?:[\s.()/-]*\d){7,12}|"
    r"0[5-7](?:[\s.()/-]*\d){8})(?!\w)"
)
_CIN = re.compile(r"(?<!\w)[A-Z]{1,2}[\s-]?\d{5,8}(?!\w)", re.IGNORECASE)
_UUID = re.compile(
    r"(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}(?![0-9a-f])",
    re.IGNORECASE,
)
_STABLE_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{24,128}(?![A-Za-z0-9_-])"
)
_DISPOSABLE_PATIENT_TOKEN = re.compile(r"(?i)\bPATIENT_[0-9a-f]{8}\b")
_EXACT_DATE = re.compile(
    r"(?<!\d)(?:"
    r"(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])"
    r"|(?:0?[1-9]|[12]\d|3[01])[-/.](?:0?[1-9]|1[0-2])[-/.](?:19|20)\d{2}"
    r")(?!\d)"
)
_EXACT_TIME = re.compile(r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?!\d)")
_COORDINATES = re.compile(
    r"(?<!\d)-?\d{1,2}\.\d{3,}\s*[,;/]\s*-?\d{1,3}\.\d{3,}(?!\d)"
)
_CLINICAL_VALUE = re.compile(
    r"(?<!\w)\d{1,4}(?:[.,]\d+)?\s*(?:"
    r"mg\s*/\s*d[lL]|mmol\s*/\s*[lL]|g\s*/\s*[lL]|mm\s*Hg|"
    r"bpm|kg|cm|%|(?:IU|UI|U)\b|unit(?:s|és?)?\b|"
    r"ملغ\s*/\s*دل|مليمول\s*/\s*ل|وحد(?:ة|ات)"
    r")",
    re.IGNORECASE,
)
_EXPLICIT_LOCATION_FIELD = re.compile(
    r"(?im)^\s*(?:adresse|address|ville|city|quartier|neighbou?rhood|"
    r"localisation|location|lieu|postal\s*code|code\s*postal|"
    r"العنوان|المدينة|الحي|الموقع|الرمز\s+البريدي)\s*[:=\-–—]\s*[^\n]+$"
)
_LOCATION_PHRASE = re.compile(
    r"(?i)\b(?:j['’]?habite\s+(?:à|a)|je\s+vis\s+(?:à|a)|"
    r"i\s+live\s+in|i\s+am\s+from|based\s+in|"
    r"(?:أسكن|اسكن|أعيش|اعيش)\s+(?:في|ب)|"
    r"(?:kan3ich|saken|sakn)\s+(?:f|fi))\s+"
    r"[^\n,.;،؛]{2,80}"
)
_EXPLICIT_ID_FIELD = re.compile(
    r"(?im)^\s*(?:patient[_\s-]*id|user[_\s-]*id|firebase[_\s-]*uid|"
    r"identifiant|identifier|username|nom|name|pr[ée]nom|first\s+name|"
    r"last\s+name|الاسم|رقم\s+المريض|معرف\s+المستخدم|"
    r"رقم\s+البطاقة\s+الوطنية|البريد\s+الإلكتروني)\s*[:=\-–—]\s*[^\n]+$"
)
_AGE_LABEL = re.compile(
    r"(?i)\b(?:age|âge|aged|âgé(?:e)?\s+de)\s*[:=]?\s*(\d{1,3})"
    r"(?:\s*(?:ans|years?(?:\s+old)?))?\b"
)
_AGE_SUFFIX = re.compile(r"(?i)(?<!\d)(\d{1,3})\s+(?:ans|years?\s+old)\b")
_AGE_ARABIC = re.compile(
    r"(?:عمري|العمر)\s*[:=]?\s*(\d{1,3})\s*(?:سنة|عام)?"
)
_AGE_DARIJA = re.compile(
    r"(?i)\b(?:3omri|omri)\s*[:=]?\s*(\d{1,3})\s*(?:3am|sna|ans?)?\b"
)


def _normalise(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).translate(_DIGIT_TRANSLATION)
    return "".join(
        " " if unicodedata.category(char) in {"Zl", "Zp", "Zs"} else char
        for char in normalized
        if unicodedata.category(char) != "Cf"
    )


def _age_band(age: int) -> str:
    if age < 0 or age > 120:
        return "[age withheld]"
    if age < 18:
        return "[age band: minor]"
    if age < 40:
        return "[age band: adult]"
    if age < 65:
        return "[age band: middle adult]"
    return "[age band: older adult]"


def _coarsen_age(pattern: re.Pattern[str], text: str) -> tuple[str, bool]:
    changed = False

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        changed = True
        try:
            return _age_band(int(match.group(1)))
        except (TypeError, ValueError):
            return "[age withheld]"

    return pattern.sub(repl, text), changed


def _replace(
    pattern: re.Pattern[str],
    replacement: str,
    text: str,
) -> tuple[str, bool]:
    updated, count = pattern.subn(replacement, text)
    return updated, count > 0


def _known_residual_findings(text: str) -> frozenset[str]:
    checks = (
        ("email", _EMAIL),
        ("phone", _PHONE),
        ("national_id", _CIN),
        ("uuid", _UUID),
        ("stable_identifier", _STABLE_TOKEN),
        ("patient_reference_token", _DISPOSABLE_PATIENT_TOKEN),
        ("exact_date", _EXACT_DATE),
        ("exact_time", _EXACT_TIME),
        ("coordinates", _COORDINATES),
        ("exact_clinical_value", _CLINICAL_VALUE),
        ("explicit_location", _EXPLICIT_LOCATION_FIELD),
        ("location_phrase", _LOCATION_PHRASE),
        ("explicit_identifier_field", _EXPLICIT_ID_FIELD),
        ("exact_age", _AGE_LABEL),
        ("exact_age", _AGE_SUFFIX),
        ("exact_age", _AGE_ARABIC),
        ("exact_age", _AGE_DARIJA),
    )
    return frozenset(name for name, pattern in checks if pattern.search(text))


def minimize_external_text(text: str) -> tuple[str, tuple[str, ...]]:
    """Deterministically reduce known re-identification signals in free text."""

    if not isinstance(text, str):
        raise TypeError("provider-bound text must be a string")

    value = _normalise(text)
    transformations: list[str] = []

    for name, pattern, replacement in (
        ("direct_identifier", _EMAIL, "[identifier withheld]"),
        ("direct_identifier", _PHONE, "[identifier withheld]"),
        ("direct_identifier", _CIN, "[identifier withheld]"),
        ("direct_identifier", _UUID, "[identifier withheld]"),
        ("direct_identifier", _STABLE_TOKEN, "[identifier withheld]"),
        ("patient_reference_token", _DISPOSABLE_PATIENT_TOKEN, "[patient reference withheld]"),
        ("explicit_identifier_field", _EXPLICIT_ID_FIELD, "[identifier field withheld]"),
        ("precise_date", _EXACT_DATE, "[date coarsened]"),
        ("precise_time", _EXACT_TIME, "[time coarsened]"),
        ("coordinates", _COORDINATES, "[location withheld]"),
        ("explicit_location", _EXPLICIT_LOCATION_FIELD, "[location withheld]"),
        ("location_phrase", _LOCATION_PHRASE, "[location withheld]"),
        ("exact_clinical_value", _CLINICAL_VALUE, "[clinical value withheld]"),
    ):
        value, changed = _replace(pattern, replacement, value)
        if changed and name not in transformations:
            transformations.append(name)

    value, changed = _coarsen_age(_AGE_LABEL, value)
    if changed:
        transformations.append("exact_age")
    value, changed = _coarsen_age(_AGE_SUFFIX, value)
    if changed and "exact_age" not in transformations:
        transformations.append("exact_age")
    value, changed = _coarsen_age(_AGE_ARABIC, value)
    if changed and "exact_age" not in transformations:
        transformations.append("exact_age")
    value, changed = _coarsen_age(_AGE_DARIJA, value)
    if changed and "exact_age" not in transformations:
        transformations.append("exact_age")

    return value, tuple(transformations)


def minimize_external_text_payload(payload: collections.abc.Mapping[str, str]) -> AnonymizationResult:
    """Minimize an exact provider-bound text payload and fail closed on residues."""

    expected = frozenset({"system_prompt", "user_prompt"})
    if frozenset(payload.keys()) != expected:
        raise AnonymizationRiskDenied(
            "external text anonymization requires exactly system_prompt and user_prompt"
        )

    minimized: dict[str, str] = {}
    all_transformations: list[str] = []
    residual: set[str] = set()

    for field_name in ("system_prompt", "user_prompt"):
        value = payload[field_name]
        if not isinstance(value, str):
            raise AnonymizationRiskDenied(
                f"external text field {field_name} must be a string"
            )
        safe_value, transformations = minimize_external_text(value)
        minimized[field_name] = safe_value
        for item in transformations:
            marker = f"{field_name}:{item}"
            if marker not in all_transformations:
                all_transformations.append(marker)
        residual.update(
            f"{field_name}:{finding}"
            for finding in _known_residual_findings(safe_value)
        )

    if residual:
        raise AnonymizationRiskDenied(
            "provider-bound text retains prohibited re-identification signals: "
            f"{sorted(residual)}"
        )

    return AnonymizationResult(
        fields=MappingProxyType(minimized),
        transformations=tuple(all_transformations),
        residual_findings=frozenset(),
    )
