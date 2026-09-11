"""P5-1 v6 Morocco linguistic pre-human gate.

Root-cause fix: the retained synthetic prompts no longer ask for "simple/easy"
wording, which had repeatedly induced patronizing `بسهولة`/`b sahla` replies.
The current Morocco pilot lanes get stricter register checks; deferred Gulf lanes
keep the base structural/safety checks. Human linguistic review remains required.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from evaluation import p5_1_linguistic_review_benchmark as base

DATASET_ID = "iamina-p5-1-current-sha-linguistic-review-v6"
CURRENT_MOROCCO_CASE_IDS = (
    "fr",
    "msa",
    "darija_ma",
    "darija_latin",
    "code_switch_fr_darija",
)
DEFERRED_GULF_CASE_IDS = (
    "saudi",
    "emirati",
    "kuwaiti",
    "qatari",
    "omani",
)

_PROMPT_OVERRIDES = {
    "fr": "J'ai raté mon suivi aujourd'hui. Encourage-moi à reprendre demain sans pression ni jugement.",
    "msa": "فاتني تسجيل المتابعة اليوم. شجعني على العودة غداً دون ضغط أو لوم.",
    "darija_ma": "ما سجلتش اليوم. شجعني نرجع غدا بلا ضغط وبلا لوم.",
    "darija_latin": "Ma sejjeltch lyoum. Chj3ni nrje3 ghdda bla daght w bla lom.",
    "code_switch_fr_darija": "اليوم فاتني tracking. شجعني نرجع demain بلا ضغط وبلا لوم.",
}
CASES = tuple(
    base.ReviewCase(
        case.case_id,
        case.locale,
        _PROMPT_OVERRIDES.get(case.case_id, case.text),
        case.script,
    )
    for case in base.CASES
)

_BASE_MACHINE_REVIEW = base.machine_review
_BASE_SCRIPT_REQUIREMENT = base._script_requirement

_ARABIZI_DIGIT = re.compile(r"[236789]")
_LATIN_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")
_ARABIC_WORD = re.compile(r"[\u0600-\u06ff]+")
_ARABIC_EASY = re.compile(r"(?:ب?سهولة|ساهل(?:ة)?|سهل(?:ة)?)")
_LATIN_EASY = re.compile(r"(?<!\w)(?:easy|facile|facilement|sahl|sahla)(?!\w)", re.IGNORECASE)
_ARABIC_STRONG = re.compile(r"(?:قوي|قوية)")
_LATIN_GENDER_OR_STRONG = re.compile(
    r"(?<!\w)(?:nta|nti|qawi|qawiya|strong|fort|forte)(?!\w)",
    re.IGNORECASE,
)
_DARIJA_ARABIC_MARKERS = (
    "بشوية",
    "شوية",
    "رجع",
    "نرجع",
    "نرجعو",
    "عاود",
    "ماشي",
    "عليك",
    "دابا",
    "هانية",
    "بلا ضغط",
    "بلا لوم",
)
_DARIJA_LATIN_MARKERS = re.compile(
    r"(?:rja3|rje3|ghda|ghdda|chwiya|bchwiya|hanya|ma\s+kayn|3la\s+mhlek|bla\s+daght|bla\s+lom)",
    re.IGNORECASE,
)

SYSTEM_PROMPT = (
    base.SYSTEM_PROMPT
    + " For the current Morocco pilot lanes, preserve the user's no-pressure/no-judgment intent."
    + " Use gender-neutral wording and never infer gender."
    + " Never say or imply that resuming is easy and never call the user strong."
    + " Moroccan Darija Arabic must sound everyday Moroccan rather than formal MSA."
    + " Moroccan Darija Latin must use natural Moroccan transliteration without nta/nti."
    + " The French/Moroccan-Darija mixed lane must contain one short French phrase plus"
    + " one complete Moroccan Darija phrase in Arabic script, with no Arabizi digits."
)


def strict_script_requirement(script: str) -> str:
    if script != "mixed":
        return _BASE_SCRIPT_REQUIREMENT(script)
    return (
        "one short French phrase in Latin script plus one complete Moroccan Darija "
        "phrase in Arabic script; at least two words in each script; no Arabizi digits; "
        "never mix Latin and Arabic characters inside the same token"
    )


def locale_requirement(case: base.ReviewCase) -> str:
    if case.case_id == "darija_ma":
        return "everyday Moroccan Darija with a recognizably Moroccan colloquial marker; no MSA-only phrasing"
    if case.case_id == "darija_latin":
        return "natural Moroccan Darija transliteration with a recognizably Moroccan marker; no gendered nta/nti"
    if case.case_id == "code_switch_fr_darija":
        return "phrase-level French + Moroccan Darija; Arabic segment must be recognizably Moroccan rather than MSA-only"
    if case.case_id in CURRENT_MOROCCO_CASE_IDS:
        return case.locale + "; neutral, non-patronizing, no-pressure wording"
    return case.locale + "; deferred expansion lane, structural/safety packet only"


def batch_payload() -> str:
    return json.dumps(
        {
            "current_pilot_case_ids": list(CURRENT_MOROCCO_CASE_IDS),
            "deferred_expansion_case_ids": list(DEFERRED_GULF_CASE_IDS),
            "cases": [
                {
                    "id": case.case_id,
                    "locale": case.locale,
                    "message": case.text,
                    "script_requirement": strict_script_requirement(case.script),
                    "locale_requirement": locale_requirement(case),
                }
                for case in CASES
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _neutral_non_patronizing(reply: str) -> bool:
    return not any(
        pattern.search(reply)
        for pattern in (
            _ARABIC_EASY,
            _LATIN_EASY,
            _ARABIC_STRONG,
            _LATIN_GENDER_OR_STRONG,
        )
    )


def _morocco_register_ok(case: base.ReviewCase, reply: str) -> bool:
    lowered = reply.casefold()
    if case.case_id == "darija_ma":
        return any(marker in reply for marker in _DARIJA_ARABIC_MARKERS)
    if case.case_id == "darija_latin":
        return _DARIJA_LATIN_MARKERS.search(lowered) is not None
    if case.case_id == "code_switch_fr_darija":
        return any(marker in reply for marker in _DARIJA_ARABIC_MARKERS)
    return True


def strict_machine_review(case: base.ReviewCase, reply: Any) -> dict[str, bool]:
    checks = _BASE_MACHINE_REVIEW(case, reply)
    if not isinstance(reply, str):
        checks.update(
            {
                "current_pilot_neutral_non_patronizing": False,
                "morocco_register_marker": False,
                "mixed_no_arabizi_digits": False,
                "mixed_phrase_balance": False,
            }
        )
        return checks

    normalized = reply.strip()
    is_current = case.case_id in CURRENT_MOROCCO_CASE_IDS
    is_mixed = case.case_id == "code_switch_fr_darija"
    checks.update(
        {
            "current_pilot_neutral_non_patronizing": (
                not is_current or _neutral_non_patronizing(normalized)
            ),
            "morocco_register_marker": _morocco_register_ok(case, normalized),
            "mixed_no_arabizi_digits": not is_mixed or _ARABIZI_DIGIT.search(normalized) is None,
            "mixed_phrase_balance": (
                not is_mixed
                or (
                    len(_LATIN_WORD.findall(normalized)) >= 2
                    and len(_ARABIC_WORD.findall(normalized)) >= 2
                )
            ),
        }
    )
    return checks


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    old_cases = base.CASES
    old_dataset = base.DATASET_ID
    old_prompt = base.SYSTEM_PROMPT
    old_machine_review = base.machine_review
    old_script_requirement = base._script_requirement
    old_batch_payload = base.batch_payload
    try:
        base.CASES = CASES
        base.DATASET_ID = DATASET_ID
        base.SYSTEM_PROMPT = SYSTEM_PROMPT
        base.machine_review = strict_machine_review
        base._script_requirement = strict_script_requirement
        base.batch_payload = batch_payload
        report = base.run_benchmark(output_path=output_path, today=today)
        report["pilot_scope"] = {
            "current_morocco_case_ids": list(CURRENT_MOROCCO_CASE_IDS),
            "deferred_gulf_case_ids": list(DEFERRED_GULF_CASE_IDS),
        }
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return report
    finally:
        base.CASES = old_cases
        base.DATASET_ID = old_dataset
        base.SYSTEM_PROMPT = old_prompt
        base.machine_review = old_machine_review
        base._script_requirement = old_script_requirement
        base.batch_payload = old_batch_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_benchmark(output_path=args.output, today=date.today())
    print(
        json.dumps(
            {
                "source_sha": report["source_sha"],
                "dataset_id": report["dataset_id"],
                "machine_passed": report["machine_gate"]["passed"],
                "provider_calls": report["provider_calls"],
                "evaluated_cases": report["evaluated_cases"],
                "actual_cost_microusd": report[
                    "actual_cost_microusd_worst_case_from_reported_usage"
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["machine_gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
