from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from diabetes.api.v1.companion import companion_next_action, companion_overview
from diabetes.services.clinical.companion_overview import (
    CompanionOverview,
    CompanionOverviewAfterVisit,
)

pytestmark = pytest.mark.django_db


def test_companion_overview_handler_is_patient_scoped_and_read_only():
    patient = get_user_model().objects.create_user(
        username="companion-overview-api",
        password="x",
    )
    request = SimpleNamespace(user=patient)
    expected = CompanionOverview(
        pattern_status="no_governed_patterns",
        review_status="insufficient_anchor",
        review_anchor_captured_at=None,
        patterns=(),
        changes_since_review=(),
        after_visit=CompanionOverviewAfterVisit(
            status="no_recorded_visit",
            anchor_id=None,
            occurred_at=None,
            source=None,
            fact_count=0,
            latest_fact_at=None,
        ),
    )

    with patch(
        "diabetes.api.v1.companion.build_companion_overview",
        return_value=expected,
    ) as build:
        payload = companion_overview(request)

    build.assert_called_once_with(patient_id=patient.id)
    assert payload["source_version"] == "companion-overview.v1"
    assert payload["after_visit"]["status"] == "no_recorded_visit"



def test_companion_next_action_exposes_exact_patient_facts_used_by_recommendation():
    patient = get_user_model().objects.create_user(
        username="companion-next-action-api",
        password="x",
    )
    request = SimpleNamespace(user=patient)
    first = __import__("django.utils.timezone", fromlist=["now"]).now()
    last = first
    facts = SimpleNamespace(
        observation_key="context:stress",
        observations=5,
        distinct_days=4,
        recurrence_count=2,
        first_observed_at=first,
        last_observed_at=last,
        evidence_density="moderate",
        evidence_window_days=90,
        personal_baseline_comparison_mg_dl=25.0,
    )
    suggestion = SimpleNamespace(
        suggestion_class="PREPARE_CLINICIAN_DISCUSSION",
        observation_key="context:stress",
        reason="existing_proactive_authority_marks_observation_review_worthy",
        proactive_state="persisting",
        change_since_review="persisting",
        patient_facts=facts,
        missing_data=(),
        limitations=("observational_association_only",),
        proactive_source_version="proactive.personal-response.lifecycle.v1",
        pattern_source_version="companion-personal-pattern-intelligence.v1",
        source_version="companion-smart-suggestions.v1",
    )
    result = SimpleNamespace(
        status="suggested",
        attention_budget="one_non_urgent_item_per_24h",
        pending_count=0,
        suggestion=suggestion,
    )

    with patch(
        "diabetes.api.v1.companion.evaluate_companion_smart_suggestion",
        return_value=result,
    ) as evaluate:
        payload = companion_next_action(request)

    evaluate.assert_called_once_with(patient_id=patient.id)
    assert payload["suggestion"]["patient_facts"] == {
        "observation_key": "context:stress",
        "observations": 5,
        "distinct_days": 4,
        "recurrence_count": 2,
        "first_observed_at": first,
        "last_observed_at": last,
        "evidence_density": "moderate",
        "evidence_window_days": 90,
        "personal_baseline_comparison_mg_dl": 25.0,
    }
