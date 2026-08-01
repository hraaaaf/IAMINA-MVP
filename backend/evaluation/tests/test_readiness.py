from dataclasses import dataclass
from datetime import date

from evaluation.readiness import build_readiness_report


@dataclass(frozen=True)
class _Manifest:
    provider: str
    model: str
    valid: bool

    def validate(self, *, today: date) -> None:
        if not self.valid:
            raise ValueError("evidence is incomplete")


def test_empty_report_is_not_ready():
    report = build_readiness_report("text", (), today=date(2026, 8, 1))
    assert report.all_ready is False


def test_report_preserves_blocking_reason_without_credentials():
    report = build_readiness_report(
        "text",
        (
            _Manifest("provider-a", "model-a", True),
            _Manifest("provider-b", "model-b", False),
        ),
        today=date(2026, 8, 1),
    )
    assert report.all_ready is False
    assert report.items[0].ready is True
    assert report.items[1].ready is False
    assert report.items[1].reason == "evidence is incomplete"
