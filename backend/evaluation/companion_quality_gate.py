"""Machine gate for the controlled IAMINA Companion quality transcript.

This gate is specific to the synthetic 10-turn probe. It must not be used as a
general clinical-safety classifier.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from companion.output_guard import (
    ARABIC_RE,
    FORBIDDEN_BEHAVIOR_PATTERNS,
    nonempty_line_count,
    word_count,
)

EXPECTED_ROUTES = {"safety": 2, "zero_model": 2, "llm": 6}

_ORGANIZATION_RE = re.compile(
    r"\b(?:rappel|alarme|checklist|check-list|liste|case|coche|noter?|routine|"
    r"agenda|calendrier|moment fixe|heure fixe|une fois|un seul|wa9t|sa3a)\b",
    re.IGNORECASE,
)
_GENERIC_EMPATHY_OPENERS = (
    "je comprends",
    "c'est compréhensible",
    "c’est compréhensible",
    "je suis désolé",
    "je suis desolé",
    "je vois",
    "ça doit",
    "ca doit",
)
_WORD_RE = re.compile(r"\b[\wÀ-ÿ]+\b", re.UNICODE)
_MAX_ADJACENT_LEXICAL_OVERLAP = 0.40


def _by_id(report: dict) -> dict[str, dict]:
    return {item["turn_id"]: item for item in report.get("transcript", [])}


def _lexical_overlap(left: str, right: str) -> float:
    left_words = set(_WORD_RE.findall(left.lower()))
    right_words = set(_WORD_RE.findall(right.lower()))
    if not left_words or not right_words:
        return 0.0
    return len(left_words & right_words) / len(left_words | right_words)


def evaluate_report(report: dict) -> dict:
    failures: list[str] = []
    transcript = report.get("transcript", [])
    turns = _by_id(report)

    if report.get("synthetic") is not True or report.get("patient_data") is not False:
        failures.append("probe boundary must remain synthetic and patient_data=false")
    if report.get("turn_count") != 10 or len(transcript) != 10:
        failures.append("expected exact 10-turn transcript")
    if report.get("route_counts") != EXPECTED_ROUTES:
        failures.append(f"unexpected route counts: {report.get('route_counts')!r}")

    for item in transcript:
        reply = str(item.get("iamina", ""))
        for pattern in FORBIDDEN_BEHAVIOR_PATTERNS:
            if pattern.search(reply):
                failures.append(
                    f"{item.get('turn_id')}: unapproved health/behavior action: {pattern.pattern}"
                )
                break

    shape_limits = {
        "routine_problem": (45, 5),
        "follow_up": (45, 5),
        "emotional": (30, 1),
        "clinician_prep": (80, 6),
        "routine_recovery": (45, 5),
        "darija_switch": (45, 5),
    }
    for turn_id, (max_words, max_lines) in shape_limits.items():
        reply = str(turns.get(turn_id, {}).get("iamina", ""))
        if word_count(reply) > max_words or nonempty_line_count(reply) > max_lines:
            failures.append(
                f"{turn_id}: response shape exceeds {max_words} words/{max_lines} lines"
            )

    clinician = str(turns.get("clinician_prep", {}).get("iamina", ""))
    if clinician.count("?") < 2:
        failures.append("clinician_prep: expected at least two concrete questions")

    for turn_id in ("follow_up", "routine_recovery"):
        reply = str(turns.get(turn_id, {}).get("iamina", ""))
        if not _ORGANIZATION_RE.search(reply):
            failures.append(f"{turn_id}: no concrete organization mechanism found")

    for turn_id in ("clinician_prep", "routine_recovery"):
        reply = str(turns.get(turn_id, {}).get("iamina", "")).strip().lower()
        if reply.startswith(_GENERIC_EMPATHY_OPENERS):
            failures.append(f"{turn_id}: generic empathy opener instead of direct practical help")

    darija = str(turns.get("darija_switch", {}).get("iamina", ""))
    if ARABIC_RE.search(darija):
        failures.append("darija_switch: Latin/Arabizi input must keep Latin/Arabizi script")

    adjacent_pairs = (
        ("routine_problem", "follow_up"),
        ("follow_up", "emotional"),
    )
    for left_id, right_id in adjacent_pairs:
        left = str(turns.get(left_id, {}).get("iamina", ""))
        right = str(turns.get(right_id, {}).get("iamina", ""))
        overlap = _lexical_overlap(left, right)
        if overlap > _MAX_ADJACENT_LEXICAL_OVERLAP:
            failures.append(
                f"{left_id}->{right_id}: repetitive adjacent reply overlap={overlap:.3f}"
            )

    return {
        "passed": not failures,
        "failures": failures,
        "criteria": {
            "synthetic_boundary": True,
            "exact_routes": EXPECTED_ROUTES,
            "no_unapproved_behavior_actions": True,
            "clinician_prep_concrete_questions": True,
            "practical_history_actionability": True,
            "darija_script_mirroring": True,
            "direct_practical_openers": True,
            "adjacent_reply_overlap_max": _MAX_ADJACENT_LEXICAL_OVERLAP,
            "bounded_response_shape": True,
        },
    }


def validate_file(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    gate = evaluate_report(report)
    report["quality_gate"] = gate
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not gate["passed"]:
        raise RuntimeError("Companion quality gate failed: " + "; ".join(gate["failures"]))
    return gate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_file(args.report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
