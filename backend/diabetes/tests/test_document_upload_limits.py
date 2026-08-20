from unittest import TestCase

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

    def test_exact_limit_is_accepted(self):
        payload = b"x" * _MAX_UPLOAD_BYTES
        upload = _FakeUpload(declared_size=_MAX_UPLOAD_BYTES, payload=payload)

        data, error = _read_upload_with_limit(upload)

        self.assertEqual(error, None)
        self.assertEqual(data, payload)
        self.assertEqual(upload.read_calls, [_MAX_UPLOAD_BYTES + 1])

    def test_empty_upload_is_rejected(self):
        upload = _FakeUpload(declared_size=0, payload=b"")

        data, error = _read_upload_with_limit(upload)

        self.assertIsNone(data)
        self.assertEqual(error, "empty")
        self.assertEqual(upload.read_calls, [_MAX_UPLOAD_BYTES + 1])
