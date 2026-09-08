import pytest

from core.contracts.domain_context import DomainContext


def test_empty_means_insufficient_data_not_runtime_failure():
    context = DomainContext.empty(language="fr")

    assert context.analysis_status == "insufficient_data"
    assert context.has_sufficient_data is False
    assert context.analysis_degradations == []
    assert context.is_degraded is False


def test_unavailable_is_explicit_and_fail_closed():
    context = DomainContext.unavailable(
        language="fr",
        degradation_codes=["kpi_query_failed"],
    )

    assert context.analysis_status == "unavailable"
    assert context.has_sufficient_data is False
    assert context.kpi_summary == {}
    assert context.detected_patterns == []
    assert context.analysis_degradations == ["kpi_query_failed"]
    assert context.is_degraded is True


def test_partial_state_can_carry_technical_degradation_without_erasing_valid_data():
    context = DomainContext(
        kpi_summary={"entries": 12},
        detected_patterns=[],
        insights=[],
        pivot_text="",
        language="fr",
        has_sufficient_data=True,
        analysis_status="partial",
        analysis_degradations=["pattern_detector_failed"],
    )

    assert context.is_degraded is True
    assert context.kpi_summary == {"entries": 12}


def test_complete_state_rejects_hidden_degradation():
    with pytest.raises(ValueError, match="complete analysis"):
        DomainContext(
            kpi_summary={},
            detected_patterns=[],
            insights=[],
            pivot_text="",
            language="fr",
            analysis_status="complete",
            analysis_degradations=["detector_failed"],
        )


def test_insufficient_data_cannot_claim_sufficient_data():
    with pytest.raises(ValueError, match="insufficient_data"):
        DomainContext(
            kpi_summary={},
            detected_patterns=[],
            insights=[],
            pivot_text="",
            language="fr",
            has_sufficient_data=True,
            analysis_status="insufficient_data",
        )
