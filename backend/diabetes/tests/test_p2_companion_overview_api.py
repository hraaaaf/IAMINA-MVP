from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from diabetes.api.v1.companion import companion_overview
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
