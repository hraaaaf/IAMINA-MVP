"""P5-1 v7 targeted MSA contract over the v6 Morocco pre-human gate.

v6 removed the ambiguous simple/easy semantics from current-Morocco prompts and
made 4/5 Morocco lanes pass. The remaining failure was MSA reintroducing
`بسهولة` despite a no-pressure/no-blame prompt. v7 therefore makes that MSA
constraint explicit while preserving the v6 Darija and mixed-language gates.
Human linguistic review remains mandatory and authoritative.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from evaluation import p5_1_linguistic_review_benchmark_v6 as base6

DATASET_ID = "iamina-p5-1-current-sha-linguistic-review-v7"
CASES = base6.CASES
CURRENT_MOROCCO_CASE_IDS = base6.CURRENT_MOROCCO_CASE_IDS
DEFERRED_GULF_CASE_IDS = base6.DEFERRED_GULF_CASE_IDS
strict_machine_review = base6.strict_machine_review
strict_script_requirement = base6.strict_script_requirement

SYSTEM_PROMPT = (
    base6.SYSTEM_PROMPT
    + " For the current MSA lane specifically, preserve the meaning of 'without pressure or blame'."
    + " Do not replace that meaning with easy/easily wording and do not use the Arabic root سهل"
    + " or forms such as بسهولة/سهل/سهلة in that MSA reply."
)


def locale_requirement(case: base6.base.ReviewCase) -> str:
    if case.case_id == "msa":
        return (
            "Modern Standard Arabic; preserve no-pressure/no-blame semantics; "
            "do not use سهل/سهلة/سهولة/بسهولة or any wording meaning easy/easily"
        )
    return base6.locale_requirement(case)


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


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    old_dataset = base6.DATASET_ID
    old_prompt = base6.SYSTEM_PROMPT
    old_batch_payload = base6.batch_payload
    try:
        base6.DATASET_ID = DATASET_ID
        base6.SYSTEM_PROMPT = SYSTEM_PROMPT
        base6.batch_payload = batch_payload
        return base6.run_benchmark(output_path=output_path, today=today)
    finally:
        base6.DATASET_ID = old_dataset
        base6.SYSTEM_PROMPT = old_prompt
        base6.batch_payload = old_batch_payload


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
