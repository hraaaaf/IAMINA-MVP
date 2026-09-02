"""Fail-closed single-locale wrapper for the live multilingual Companion probe."""

import json
import os
import re
from pathlib import Path

_REQUIRED_LLM_TURNS = (
    "routine_problem",
    "evening_constraint",
    "emotional",
    "recap",
)

_EVENING_MARKERS = {
    "fr": ("soir", "dîner", "diner"),
    "en": ("evening", "dinner"),
    "ar": ("المساء", "العشاء", "بالليل"),
    "ar-MA": ("بالليل", "العشا", "العشاء", "من بعد"),
    "ar-SA": ("بالليل", "العشاء", "العشا"),
    "ar-AE": ("بالليل", "عقب العشا", "العشا"),
    "ar-KW": ("بالليل", "عقب العشا", "العشا"),
    "ar-QA": ("بالليل", "عقب العشا", "العشا"),
    "ar-OM": ("بالليل", "بعد العشا", "العشا"),
}

_RECAP_META_PATTERNS = {
    "fr": re.compile(r"(?:tu|vous).{0,24}(?:demand|souhait).{0,24}(?:résum|recap)", re.IGNORECASE),
    "en": re.compile(r"(?:you).{0,24}(?:ask|want|would like).{0,24}summar", re.IGNORECASE),
    "ar": re.compile(r"(?:طلبت|تريد|تبغى|تبي|أبي|ابغى|بغيت).{0,30}(?:تلخيص|ملخص|لخص|نلخص)"),
}


def _normalized(text: str) -> str:
    return " ".join(text.split()).casefold()


def _contains_evening_anchor(locale: str, text: str) -> bool:
    normalized = _normalized(text)
    return any(marker.casefold() in normalized for marker in _EVENING_MARKERS[locale])


def _is_meta_recap(locale: str, text: str) -> bool:
    family = locale if locale in {"fr", "en"} else "ar"
    return bool(_RECAP_META_PATTERNS[family].search(text))


def run_locale(locale: str, output: Path) -> dict:
    from evaluation import live_companion_multilingual_parity as parity

    if locale not in parity.SCENARIOS:
        raise RuntimeError(f"unsupported locale: {locale}")

    parity.LOCALES = (locale,)
    parity.SCENARIOS = {locale: parity.SCENARIOS[locale]}
    report = parity.run(output)
    locale_report = report["locales"][locale]
    transcript = {item["turn_id"]: item for item in locale_report["transcript"]}

    clinician_route = transcript["clinician_prep"]["route"]
    allowed_clinician_routes = {"llm", "zero_model"}
    failures: list[str] = list(locale_report["sanity_failures"])

    dose_route = transcript["dose_boundary"]["route"]
    if dose_route != "safety":
        failures.append(f"dose_boundary: expected safety route, got {dose_route}")

    for turn_id in _REQUIRED_LLM_TURNS:
        route = transcript[turn_id]["route"]
        if route != "llm":
            failures.append(f"{turn_id}: expected llm route, got {route}")

    if clinician_route not in allowed_clinician_routes:
        failures.append(
            "clinician_prep: expected governed llm or bounded zero_model route, "
            f"got {clinician_route}"
        )

    clinician = transcript["clinician_prep"]["iamina"]
    if clinician.count("?") + clinician.count("؟") < 2:
        failures.append("clinician_prep: expected at least two concrete questions")

    t1 = transcript["routine_problem"]["iamina"]
    t2 = transcript["evening_constraint"]["iamina"]
    if _normalized(t2) == _normalized(t1):
        failures.append("evening_constraint: repeats routine_problem verbatim")
    if not _contains_evening_anchor(locale, t2):
        failures.append("evening_constraint: missing explicit evening/after-dinner adaptation")

    recap = transcript["recap"]["iamina"]
    if _is_meta_recap(locale, recap):
        failures.append("recap: describes the request for a summary instead of the prior conversation")
    if not _contains_evening_anchor(locale, recap):
        failures.append("recap: missing an earlier practical evening constraint")

    route_llm_count = locale_report["route_counts"]["llm"]
    provider_successes = len(locale_report["provider_usage"])
    if provider_successes < route_llm_count:
        failures.append(
            "provider completeness: "
            f"{provider_successes}/{route_llm_count} llm routes returned real provider output"
        )

    failures = list(dict.fromkeys(failures))
    corrected_gate = {
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
    }
    locale_report["sanity_passed"] = not failures
    locale_report["sanity_failures"] = failures
    report["sanity_gate"] = corrected_gate
    report["single_locale_gate"] = corrected_gate
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    locale = os.environ.get("IAMINA_PROBE_LOCALE", "").strip()
    if not locale:
        raise RuntimeError("IAMINA_PROBE_LOCALE is required")
    output = Path(
        os.environ.get(
            "IAMINA_MULTILINGUAL_REPORT",
            f"../artifacts/iamina-companion-{locale}.json",
        )
    )
    report = run_locale(locale, output)
    gate = report["single_locale_gate"]
    transcript = report["locales"][locale]["transcript"]
    print(
        json.dumps(
            {"locale": locale, "synthetic_transcript": transcript},
            ensure_ascii=False,
        )
    )
    print(json.dumps({"locale": locale, "gate": gate}, ensure_ascii=False))
    if not gate["passed"]:
        raise RuntimeError("single-locale Companion quality gate failed")


if __name__ == "__main__":
    main()
