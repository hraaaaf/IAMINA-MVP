from datetime import datetime, timezone

import pytest

from evaluation.decision import ProviderDecision
from evaluation.reporting import build_report
from evaluation.runner import CaseRun


def test_report_is_versioned_and_reproducible():
    run = CaseRun(
        case_id="eval_case",
        provider="provider-a",
        output={"ok": True},
        latency_ms=12.5,
        dataset_fingerprint="a" * 64,
    )
    decision = ProviderDecision(
        modality="text",
        selected_provider="provider-a",
        ranked_providers=("provider-a",),
        rejected={},
    )
    report = build_report(
        (run,),
        (decision,),
        generated_at=datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
    )
    assert report.schema_version == "1.0"
    assert report.generated_at == "2026-08-01T12:00:00+00:00"
    assert report.dataset_fingerprints == ("a" * 64,)
    assert report.decisions[0]["selected_provider"] == "provider-a"


def test_report_rejects_naive_timestamp():
    with pytest.raises(ValueError):
        build_report((), (), generated_at=datetime(2026, 8, 1, 12, 0))
