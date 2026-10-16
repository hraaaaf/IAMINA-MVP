"""Ensure synthetic-only W01-G6 script cannot target remote Neon by configuration."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[2] /
          "backend/scripts/w01_pg16_backup_restore_ci.sh").read_text(encoding="utf-8")


class W01G6Guard(unittest.TestCase):
    def test_exact_ci_and_database_gate(self):
        self.assertIn('"$GITHUB_ACTIONS" != "true"', SOURCE)
        self.assertIn('"$CI" != "true"', SOURCE)
        self.assertIn('127.0.0.1:5432/iamina_w01_ci', SOURCE)

    def test_disposable_restore_database(self):
        self.assertIn('source_db=iamina_w01_ci', SOURCE)
        self.assertIn('restore_db=iamina_w01_restore', SOURCE)
        self.assertIn('restore target already exists', SOURCE)

    def test_actual_pg16_dump_restore_and_rollback(self):
        for fragment in ('postgres:16-alpine', 'pg_dump', 'pg_restore',
                         'W01_FAKE_DATA_ONLY', 'ROLLBACK;', 'migrate --check'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, SOURCE)

    def test_no_external_database(self):
        for fragment in ('neon.tech', 'vercel.app', 'square-sun-82359137'):
            self.assertNotIn(fragment, SOURCE)


if __name__ == "__main__":
    unittest.main()
