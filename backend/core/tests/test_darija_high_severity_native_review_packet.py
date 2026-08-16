import json
import pathlib

_PACKET = pathlib.Path(__file__).parent / "fixtures" / "darija_high_severity_native_review_packet.json"
_OUTCOMES = pathlib.Path(__file__).parent / "fixtures" / "darija_high_severity_native_review_outcomes.json"


def _packet_rows():
    return json.loads(_PACKET.read_text(encoding="utf-8"))


def _outcome_rows():
    return json.loads(_OUTCOMES.read_text(encoding="utf-8"))


def _runtime_inventory():
    from core.triage_classification import glycemic_emergency_variant_inventory

    return {
        (variant.input_form, variant.text)
        for variant in glycemic_emergency_variant_inventory()
        if variant.locale == "ar-MA"
    }


def test_native_review_packet_exactly_matches_current_ar_ma_high_severity_inventory():
    packet = {(row["input_form"], row["text"]) for row in _packet_rows()}
    runtime = _runtime_inventory()

    assert len(packet) == 36
    assert packet == runtime


def test_native_review_packet_is_fail_closed_for_restricted_approval():
    rows = _packet_rows()

    assert rows
    assert all(row["restricted_approval"] is False for row in rows)
    assert {row["native_evidence_status"] for row in rows} <= {
        "pending_exact_review",
        "prior_exact_native_evidence",
        "accepted_exact_native_evidence",
        "rejected_exact_native_evidence",
    }


def test_prior_exact_native_evidence_is_limited_to_recorded_batch_evidence():
    prior = {
        row["text"]
        for row in _packet_rows()
        if row["native_evidence_status"] == "prior_exact_native_evidence"
    }

    assert prior == {"غادي يغمى عليا", "كنترعد", "كنرجف"}


def test_completed_native_review_outcomes_exactly_cover_runtime_inventory():
    rows = _outcome_rows()
    outcomes = {(row["input_form"], row["text"]) for row in rows}

    assert len(rows) == 36
    assert len(outcomes) == 36
    assert outcomes == _runtime_inventory()
    assert all(
        row["native_evidence_status"]
        in {"accepted_exact_native_evidence", "rejected_exact_native_evidence"}
        for row in rows
    )
    assert all(row["restricted_approval"] is False for row in rows)


def test_completed_native_review_outcomes_preserve_recorded_decisions():
    outcomes = {row["text"]: row["native_evidence_status"] for row in _outcome_rows()}

    assert outcomes["ghadi ntih"] == "accepted_exact_native_evidence"
    assert outcomes["ghadi ntah"] == "rejected_exact_native_evidence"
    assert outcomes["غادي يغمى عليا"] == "rejected_exact_native_evidence"
    assert outcomes["kanrjef"] == "accepted_exact_native_evidence"
    assert outcomes["kanr3ed"] == "rejected_exact_native_evidence"
    assert outcomes["ma kan7mlch"] == "accepted_exact_native_evidence"
    assert outcomes["dwakht"] == "rejected_exact_native_evidence"
    assert outcomes["ma kanchoufch"] == "rejected_exact_native_evidence"
    assert outcomes["ما كنشوف والو"] == "accepted_exact_native_evidence"
