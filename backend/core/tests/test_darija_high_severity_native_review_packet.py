import json
from pathlib import Path

from core.triage_classification import glycemic_emergency_variant_inventory


_PACKET = Path(__file__).parent / "fixtures" / "darija_high_severity_native_review_packet.json"


def _packet_rows():
    return json.loads(_PACKET.read_text(encoding="utf-8"))


def test_native_review_packet_exactly_matches_current_ar_ma_high_severity_inventory():
    packet = {(row["input_form"], row["text"]) for row in _packet_rows()}
    runtime = {
        (variant.input_form, variant.text)
        for variant in glycemic_emergency_variant_inventory()
        if variant.locale == "ar-MA"
    }

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
