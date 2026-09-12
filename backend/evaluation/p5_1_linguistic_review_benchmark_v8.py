"""P5-1 v8 human-feedback refinement over the retained v7 Morocco packet.

A competent human review accepted the overall v7 direction but corrected two
Morocco Darija formulations. v8 encodes those concrete register findings while
preserving the v7 MSA and safety constraints. Human review remains authoritative.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from evaluation import p5_1_linguistic_review_benchmark_v7 as base7

DATASET_ID = "iamina-p5-1-current-sha-linguistic-review-v8"
CURRENT_MOROCCO_CASE_IDS = base7.CURRENT_MOROCCO_CASE_IDS
DEFERRED_GULF_CASE_IDS = base7.DEFERRED_GULF_CASE_IDS
strict_script_requirement = base7.strict_script_requirement

_PROMPT_OVERRIDES = {
    "darija_latin": (
        "Ma sejjeltch lyoum. Chj3ni bach n9der n3awed ghdda bla daght w bla lom, "
        "b jomla katkhatebni ana direct."
    ),
}
CASES = tuple(
    base7.base6.base.ReviewCase(
        case.case_id,
        case.locale,
        _PROMPT_OVERRIDES.get(case.case_id, case.text),
        case.script,
    )
    for case in base7.CASES
)

_DARIJA_AR_REJECT = re.compile(r"ما\s*تشدش")
_DARIJA_LATIN_REJECT = re.compile(r"(?<!\w)nrj3(?!\w)", re.IGNORECASE)
_DARIJA_LATIN_RETURN = re.compile(
    r"(?<!\w)(?:t9der|t9dar)\s+(?:terja3|trja3|t3awed|t3awd)(?!\w)",
    re.IGNORECASE,
)

SYSTEM_PROMPT = (
    base7.SYSTEM_PROMPT
    + " Retained human Morocco review: for Darija Arabic, prefer natural reassurance such as ما تقلقش"
    + " and avoid ما تشدش in this context."
    + " For Darija Latin, address the user directly in second person with an explicit ability-to-resume phrase"
    + " such as t9der terja3 or t9der t3awed; never answer with first-person-plural nrj3."
)


def locale_requirement(case: base7.base6.base.ReviewCase) -> str:
    if case.case_id == "darija_ma":
        return (
            base7.locale_requirement(case)
            + "; retained human correction: avoid ما تشدش; natural reassurance like ما تقلقش is preferred"
        )
    if case.case_id == "darija_latin":
        return (
            base7.locale_requirement(case)
            + "; retained human correction: address the user directly in second person with t9der/t9dar plus a return verb; avoid nrj3"
        )
    return base7.locale_requirement(case)


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


def strict_machine_review(case: base7.base6.base.ReviewCase, reply: Any) -> dict[str, bool]:
    checks = base7.strict_machine_review(case, reply)
    if not isinstance(reply, str):
        checks["retained_human_darija_feedback"] = False
        return checks

    if case.case_id == "darija_ma":
        checks["retained_human_darija_feedback"] = _DARIJA_AR_REJECT.search(reply) is None
    elif case.case_id == "darija_latin":
        checks["retained_human_darija_feedback"] = (
            _DARIJA_LATIN_REJECT.search(reply) is None
            and _DARIJA_LATIN_RETURN.search(reply) is not None
        )
    else:
        checks["retained_human_darija_feedback"] = True
    return checks


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    effective = base7.base6
    old_dataset = effective.DATASET_ID
    old_cases = effective.CASES
    old_prompt = effective.SYSTEM_PROMPT
    old_batch_payload = effective.batch_payload
    old_machine_review = effective.strict_machine_review
    try:
        effective.DATASET_ID = DATASET_ID
        effective.CASES = CASES
        effective.SYSTEM_PROMPT = SYSTEM_PROMPT
        effective.batch_payload = batch_payload
        effective.strict_machine_review = strict_machine_review
        report = effective.run_benchmark(output_path=output_path, today=today)
        report["dataset_id"] = DATASET_ID
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
        effective.DATASET_ID = old_dataset
        effective.CASES = old_cases
        effective.SYSTEM_PROMPT = old_prompt
        effective.batch_payload = old_batch_payload
        effective.strict_machine_review = old_machine_review


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
