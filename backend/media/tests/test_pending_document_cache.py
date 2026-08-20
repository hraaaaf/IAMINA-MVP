from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from media.documents.pending_cache import (
    pending_extraction_pattern,
    purge_patient_pending_extractions,
)


class PendingExtractionCacheTest(SimpleTestCase):
    def test_pattern_is_patient_scoped(self):
        self.assertEqual(pending_extraction_pattern(7), "pulper:pending:7:*")

    def test_pattern_rejects_invalid_patient_id(self):
        for patient_id in (0, -1, "7"):
            with self.subTest(patient_id=patient_id):
                with self.assertRaises(ValueError):
                    purge_patient_pending_extractions(patient_id)  # type: ignore[arg-type]

    def test_purge_scans_keys_only_and_deletes_matches(self):
        redis = MagicMock()
        redis.scan_iter.return_value = iter([b"key-a", b"key-b"])
        redis.delete.return_value = 2

        with (
            patch(
                "media.documents.pending_cache.get_redis_connection",
                return_value=redis,
            ) as get_connection,
            patch(
                "media.documents.pending_cache.cache.make_key",
                return_value="amina:1:pulper:pending:7:*",
            ) as make_key,
        ):
            deleted = purge_patient_pending_extractions(7)

        self.assertEqual(deleted, 2)
        get_connection.assert_called_once_with("default")
        make_key.assert_called_once_with("pulper:pending:7:*")
        redis.scan_iter.assert_called_once_with(
            match="amina:1:pulper:pending:7:*",
            count=100,
        )
        redis.delete.assert_called_once_with(b"key-a", b"key-b")

    def test_purge_is_idempotent_when_no_keys_remain(self):
        redis = MagicMock()
        redis.scan_iter.return_value = iter([])

        with (
            patch(
                "media.documents.pending_cache.get_redis_connection",
                return_value=redis,
            ),
            patch(
                "media.documents.pending_cache.cache.make_key",
                return_value="amina:1:pulper:pending:7:*",
            ),
        ):
            deleted = purge_patient_pending_extractions(7)

        self.assertEqual(deleted, 0)
        redis.delete.assert_not_called()

    def test_redis_failure_propagates_for_fail_closed_erasure(self):
        redis = MagicMock()
        redis.scan_iter.side_effect = RuntimeError("redis unavailable")

        with (
            patch(
                "media.documents.pending_cache.get_redis_connection",
                return_value=redis,
            ),
            patch(
                "media.documents.pending_cache.cache.make_key",
                return_value="amina:1:pulper:pending:7:*",
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "redis unavailable"):
                purge_patient_pending_extractions(7)
