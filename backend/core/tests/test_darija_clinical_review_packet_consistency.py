# ruff: noqa: I001

from pathlib import Path
import json


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "backend" / "core" / "tests" / "fixtures"
PACKET = (
    REPO_ROOT
    / "docs"
    / "evaluation"
    / "DARIJA_HIGH_SEVERITY_CLINICAL_REVIEW_PACKET.md"
)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_native_review_sources_and_remediation_plan_are_disjoint_and_exact() -> None:
    outcomes = _load_json(FIXTURES / "darija_high_severity_native_review_outcomes.json")
    plan = _load_json(FIXTURES / "darija_high_severity_runtime_remediation_plan.json")

    accepted = {
        row["text"]
        for row in outcomes
        if row["native_evidence_status"] == "accepted_exact_native_evidence"
    }
    rejected = {
        row["text"]
        for row in outcomes
        if row["native_evidence_status"] == "rejected_exact_native_evidence"
    }
    planned_rejections = {row["text"] for row in plan["rejected_runtime_variants"]}

    assert accepted.isdisjoint(rejected)
    assert planned_rejections == rejected
    assert accepted.isdisjoint(planned_rejections)

    for candidate in plan["pending_replacements"]:
        assert candidate["runtime_authorized"] is False
        assert candidate["restricted_approval"] is False


def test_clinical_review_packet_matches_native_review_outcomes() -> None:
    outcomes = _load_json(FIXTURES / "darija_high_severity_native_review_outcomes.json")
    packet = PACKET.read_text(encoding="utf-8")

    accepted_section = packet.split(
        "### Existing runtime variants accepted by native review", 1
    )[1].split("### Existing runtime variants rejected by native review", 1)[0]
    rejected_section = packet.split(
        "### Existing runtime variants rejected by native review", 1
    )[1].split("### Native replacement candidates, not runtime-authorized", 1)[0]

    for row in outcomes:
        token = f"`{row['text']}`"
        if row["native_evidence_status"] == "accepted_exact_native_evidence":
            assert token in accepted_section
            assert token not in rejected_section
        else:
            assert token in rejected_section
            assert token not in accepted_section
