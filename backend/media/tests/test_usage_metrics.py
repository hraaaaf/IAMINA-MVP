from __future__ import annotations

from unittest import TestCase

from media.usage_metrics import aggregate_media_usage


class MediaUsageMetricsTest(TestCase):
    def test_synthetic_egress_fixture_aggregates_observed_bytes_per_mau(self):
        events = [
            {
                "event": "media_bytes",
                "action": "uploaded",
                "bytes": 1000,
                "retention_class": "TRANSIENT_EXTRACTION",
            },
            {
                "event": "media_bytes",
                "action": "uploaded",
                "bytes": 500,
                "retention_class": "TRANSIENT_EXTRACTION",
            },
            {
                "event": "media_bytes",
                "action": "retained",
                "bytes": 800,
                "retention_class": "PATIENT_RETAINED",
            },
            {
                "event": "media_bytes",
                "action": "downloaded",
                "bytes": 250,
                "retention_class": "PATIENT_RETAINED",
            },
            {
                "event": "media_bytes",
                "action": "deleted",
                "bytes": 800,
                "retention_class": "PATIENT_RETAINED",
            },
            {"event": "llm_usage", "status": "success"},
        ]

        report = aggregate_media_usage(events, active_users=10)

        self.assertEqual(report["media_events"], 5)
        self.assertEqual(report["action_counts"]["uploaded"], 2)
        self.assertEqual(report["bytes_by_action"]["uploaded"], 1500)
        self.assertEqual(report["bytes_by_action"]["downloaded"], 250)
        self.assertEqual(report["uploaded_bytes_per_mau"], 150.0)
        self.assertEqual(report["downloaded_bytes_per_mau"], 25.0)
        self.assertEqual(
            report["bytes_by_retention_class"],
            {"PATIENT_RETAINED": 1850, "TRANSIENT_EXTRACTION": 1500},
        )

    def test_missing_mau_denominator_remains_missing_not_zero(self):
        report = aggregate_media_usage(
            [
                {
                    "event": "media_bytes",
                    "action": "downloaded",
                    "bytes": 100,
                    "retention_class": "PATIENT_RETAINED",
                }
            ]
        )

        self.assertIsNone(report["uploaded_bytes_per_mau"])
        self.assertIsNone(report["downloaded_bytes_per_mau"])

    def test_empty_complete_stream_with_known_mau_reports_zero_observed_bytes(self):
        report = aggregate_media_usage([], active_users=5)

        self.assertEqual(report["uploaded_bytes_per_mau"], 0.0)
        self.assertEqual(report["downloaded_bytes_per_mau"], 0.0)

    def test_storage_occupancy_and_cost_are_not_inferred_from_lifecycle_events(self):
        report = aggregate_media_usage(
            [
                {
                    "event": "media_bytes",
                    "action": "retained",
                    "bytes": 1000,
                    "retention_class": "PATIENT_RETAINED",
                }
            ],
            active_users=1,
        )

        self.assertIsNone(report["storage_occupancy_bytes"])
        self.assertEqual(
            report["storage_occupancy_status"],
            "unavailable_without_time_weighted_retained_object_inventory",
        )
        self.assertIsNone(report["storage_cost_per_mau"])
        self.assertIsNone(report["egress_cost_per_mau"])

    def test_malformed_known_media_events_fail_closed(self):
        bad_events = [
            {
                "event": "media_bytes",
                "action": "public",
                "bytes": 1,
                "retention_class": "x",
            },
            {
                "event": "media_bytes",
                "action": "uploaded",
                "bytes": -1,
                "retention_class": "x",
            },
            {
                "event": "media_bytes",
                "action": "uploaded",
                "bytes": True,
                "retention_class": "x",
            },
            {
                "event": "media_bytes",
                "action": "uploaded",
                "bytes": 1,
                "retention_class": "",
            },
        ]

        for event in bad_events:
            with self.subTest(event=event):
                with self.assertRaises(ValueError):
                    aggregate_media_usage([event], active_users=1)

    def test_invalid_active_user_denominator_fails_closed(self):
        for active_users in (0, -1, True, 1.5):
            with self.subTest(active_users=active_users):
                with self.assertRaises(ValueError):
                    aggregate_media_usage([], active_users=active_users)
