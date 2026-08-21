from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connection
from django.utils import timezone

from core.models import AIUserThrottleWindow
from llm.user_abuse_throttle import (
    PersistentUserAbuseThrottle,
    UserAbuseThrottleExceeded,
    UserAbuseThrottlePolicy,
)


def _throttle(max_requests=2):
    return PersistentUserAbuseThrottle(
        policy=UserAbuseThrottlePolicy(window_seconds=3600, max_requests=max_requests),
        key_material=b"frug8-user-throttle-test-key-material-32-bytes-plus",
    )


@pytest.mark.django_db(transaction=True)
def test_persistent_user_throttle_is_hmac_only_and_resets_next_window(caplog):
    throttle = _throttle(max_requests=1)
    now = timezone.now()

    assert throttle.authorize(patient_id=42, now=now) == 1
    with caplog.at_level("WARNING", logger="iamina.cost"):
        with pytest.raises(UserAbuseThrottleExceeded):
            throttle.authorize(patient_id=42, now=now)
    alert = "\n".join(record.getMessage() for record in caplog.records)
    assert "user_throttle_exceeded" in alert
    assert "patient" not in alert
    assert "hmac256:" not in alert
    assert throttle.authorize(patient_id=42, now=now + timedelta(hours=1)) == 1

    rows = list(AIUserThrottleWindow.objects.order_by("window_start"))
    assert len(rows) == 2
    assert all(row.subject_key.startswith("hmac256:") for row in rows)
    assert all(len(row.subject_key) == 72 for row in rows)
    assert all("patient" not in row.subject_key for row in rows)


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_user_throttle_never_exceeds_ceiling():
    if connection.vendor != "postgresql":
        pytest.skip("row-lock concurrency proof requires PostgreSQL")

    throttle = _throttle(max_requests=2)
    now = timezone.now()
    barrier = Barrier(3)

    def worker():
        close_old_connections()
        try:
            barrier.wait()
            throttle.authorize(patient_id=77, now=now)
            return "allowed"
        except UserAbuseThrottleExceeded:
            return "blocked"
        finally:
            # Worker threads own independent Django connections. Close them
            # explicitly so the transactional concurrency proof leaves no
            # PostgreSQL sessions behind at test-database teardown.
            connection.close()

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda _: worker(), range(3)))

    assert results.count("allowed") == 2
    assert results.count("blocked") == 1
    row = AIUserThrottleWindow.objects.get()
    assert row.request_count == 2
