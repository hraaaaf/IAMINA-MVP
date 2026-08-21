from unittest import TestCase
from unittest.mock import patch

from diabetes.api.v1.documents import _MAX_UPLOAD_BYTES, _read_upload_with_limit


class _FakeUpload:
    def __init__(self, *, declared_size, payload: bytes):
        self.size = declared_size
        self._payload = payload
        self.read_calls: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_calls.append(size)
        if size < 0:
            return self._payload
        return self._payload[:size]


class DocumentUploadLimitTest(TestCase):
    def test_declared_oversize_is_rejected_before_read(self):
        upload = _FakeUpload(
            declared_size=_MAX_UPLOAD_BYTES + 1,
            payload=b"x",
        )

        data, error = _read_upload_with_limit(upload)

        self.assertIsNone(data)
        self.assertEqual(error, "too_large")
        self.assertEqual(upload.read_calls, [])

    def test_unknown_size_uses_bounded_defensive_read(self):
        upload = _FakeUpload(
            declared_size=None,
            payload=b"x" * (_MAX_UPLOAD_BYTES + 2),
        )

        data, error = _read_upload_with_limit(upload)

        self.assertIsNone(data)
        self.assertEqual(error, "too_large")
        self.assertEqual(upload.read_calls, [_MAX_UPLOAD_BYTES + 1])

    @patch("diabetes.api.v1.documents.record_media_bytes")
    def test_exact_limit_is_accepted_and_records_ingress_bytes(self, record_media_bytes):
        payload = b"x" * _MAX_UPLOAD_BYTES
        upload = _FakeUpload(declared_size=_MAX_UPLOAD_BYTES, payload=payload)

        data, error = _read_upload_with_limit(upload)

        self.assertEqual(error, None)
        self.assertEqual(data, payload)
        self.assertEqual(upload.read_calls, [_MAX_UPLOAD_BYTES + 1])
        record_media_bytes.assert_called_once_with(
            action="uploaded",
            byte_count=_MAX_UPLOAD_BYTES,
            retention_class="TRANSIENT_EXTRACTION",
        )

    def test_empty_upload_is_rejected(self):
        upload = _FakeUpload(declared_size=0, payload=b"")

        data, error = _read_upload_with_limit(upload)

        self.assertIsNone(data)
        self.assertEqual(error, "empty")
        self.assertEqual(upload.read_calls, [_MAX_UPLOAD_BYTES + 1])
