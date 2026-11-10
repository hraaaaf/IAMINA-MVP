"""Regression tests for the production HTTP logging privacy gate."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_flutter_http_logging import violations


class FlutterHttpLoggingGateTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "services").mkdir()

    def write_client(self, source: str):
        (self.root / "services" / "api_client.dart").write_text(
            source, encoding="utf-8"
        )

    def test_clean_transport_passes(self):
        self.write_client("interceptors: [AuthInterceptor(authService)],")
        self.assertEqual(violations(self.root), [])

    def test_curl_after_auth_is_rejected(self):
        self.write_client(
            "interceptors: [AuthInterceptor(authService), CurlInterceptor()],"
        )
        self.assertTrue(violations(self.root))

    def test_logging_in_other_production_file_is_rejected(self):
        self.write_client("AuthInterceptor(authService)")
        (self.root / "other.dart").write_text(
            "final leak = LoggingInterceptor();", encoding="utf-8"
        )
        self.assertTrue(violations(self.root))

    def test_missing_client_fails_closed(self):
        self.assertTrue(violations(self.root))

    def test_missing_auth_interceptor_fails_closed(self):
        self.write_client("interceptors: []")
        self.assertTrue(violations(self.root))


if __name__ == "__main__":
    unittest.main()
