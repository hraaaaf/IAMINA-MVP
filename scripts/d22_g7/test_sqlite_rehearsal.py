"""D22 G7 rehearsal: Python stdlib SQLite, SYNTHETIC fixtures ONLY.

NOT imported by Flutter, backend, migrations, Vercel or any patient runtime.
It does NOT establish clinical, privacy, browser or auth certification.
Run only via: python -m unittest discover -s scripts/d22_g7 -p 'test_*.py' -v
"""

import hashlib
import math
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path


# SQLite v12 subset faithfully mirrors the relevant Drift column meanings,
# not the entire generated Drift schema. This is NOT a production migration.
FIXTURE_SQL = """
CREATE TABLE patient_profiles (
  user_id INTEGER PRIMARY KEY,
  target_range_low REAL NOT NULL DEFAULT 70.0,
  target_range_high REAL NOT NULL DEFAULT 180.0,
  unit_preference TEXT NOT NULL DEFAULT 'mg/dL'
);
CREATE TABLE log_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  blood_sugar REAL NOT NULL,
  client_uuid TEXT NOT NULL UNIQUE,
  source TEXT NOT NULL DEFAULT 'manual'
);
PRAGMA user_version = 12;
"""

# Candidate schema ONLY; do not place in AppDatabase.migration/onCreate.
# No default source unit: unknown historic records are deliberately unlinked.
# A sidecar avoids rewriting blood_sugar or legacy target_range columns.
EVIDENCE_SQL = """
CREATE TABLE glucose_measurement_evidence_v1 (
  log_entry_id INTEGER PRIMARY KEY,
  original_source_value REAL NOT NULL CHECK (original_source_value > 0),
  original_source_unit_ucum TEXT NOT NULL
    CHECK (original_source_unit_ucum IN ('mg/dL', 'mmol/L')),
  unit_system TEXT NOT NULL CHECK (unit_system = 'http://unitsofmeasure.org'),
  provenance TEXT NOT NULL CHECK (provenance = 'user_entered'),
  conversion_contract TEXT NOT NULL
    CHECK (conversion_contract = 'nist_glucose_1801559_v1'),
  recorded_at_utc TEXT NOT NULL CHECK (length(recorded_at_utc) > 0),
  FOREIGN KEY (log_entry_id) REFERENCES log_entries(id) ON DELETE CASCADE
)
"""

PHYSICAL_CONVERSION_CANDIDATE = 18.01559


def connect_fixture(path: Path, patient_id: int) -> sqlite3.Connection:
    """Create a brand-new disposable DB, never open an existing user vault."""
    if path.exists():
        raise ValueError("Refusing existing database path in synthetic fixture")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(FIXTURE_SQL)
    conn.execute(
        "INSERT INTO patient_profiles(user_id) VALUES (?)", (patient_id,)
    )
    conn.executemany(
        "INSERT INTO log_entries(blood_sugar, client_uuid) VALUES (?, ?)",
        [(70.0, f"synthetic-{patient_id}-low"),
         (180.0, f"synthetic-{patient_id}-high")],
    )
    conn.commit()
    return conn


def snapshot_legacy(conn: sqlite3.Connection) -> tuple:
    return (
        tuple(conn.execute(
            "SELECT id, blood_sugar, client_uuid, source "
            "FROM log_entries ORDER BY id"
        )),
        tuple(conn.execute(
            "SELECT user_id, target_range_low, target_range_high, "
            "unit_preference FROM patient_profiles ORDER BY user_id"
        )),
        conn.execute("PRAGMA user_version").fetchone()[0],
    )


def table_exists(conn: sqlite3.Connection) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='glucose_measurement_evidence_v1'"
    ).fetchone() is not None


def add_sidecar_synthetic_only(
    conn: sqlite3.Connection, *, inject_failure: bool = False
) -> None:
    """Atomically create metadata-only schema; NEVER backfill old readings.

    The caller must provide a synthetic/test connection. This function is
    deliberately not callable through CLI with a database path.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        existing = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' "
            "AND name='glucose_measurement_evidence_v1'"
        ).fetchone()
        if existing:
            canonical = lambda sql: "".join(sql.lower().split()).rstrip(";")
            if canonical(existing[0]) != canonical(EVIDENCE_SQL):
                raise RuntimeError("Conflicting sidecar schema; fail closed")
        else:
            conn.execute(EVIDENCE_SQL)
        if inject_failure:
            raise RuntimeError("Synthetic injected migration failure")
        conn.commit()
    except BaseException:
        conn.rollback()
        raise


def write_new_synthetic_evidence(
    conn: sqlite3.Connection, *,
    log_id: int, raw_value: float, declared_unit: str
) -> None:
    """Only new, explicitly declared synthetic entries, no legacy backfill."""
    if declared_unit not in ("mg/dL", "mmol/L"):
        raise ValueError("Source unit must be explicit UCUM mg/dL or mmol/L")
    if not math.isfinite(raw_value) or raw_value <= 0:
        raise ValueError("Source value must be finite and positive")
    canonical = raw_value * (
        PHYSICAL_CONVERSION_CANDIDATE if declared_unit == "mmol/L" else 1
    )
    if not math.isfinite(canonical) or canonical <= 0:
        raise ValueError("Overflow or underflow in canonical projection")
    conn.execute(
        "INSERT INTO glucose_measurement_evidence_v1 "
        "(log_entry_id, original_source_value, original_source_unit_ucum, "
        "unit_system, provenance, conversion_contract, recorded_at_utc) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (log_id, raw_value, declared_unit, "http://unitsofmeasure.org",
         "user_entered", "nist_glucose_1801559_v1",
         "2026-11-02T00:00:00Z"),
    )


def backup_snapshot(conn: sqlite3.Connection, path: Path) -> str:
    """SQLite online backup snapshot and SHA256; synthetic files only."""
    if path.exists():
        raise ValueError("Backup target already exists; refusing overwrite")
    with sqlite3.connect(path) as dest:
        conn.backup(dest)
    return hashlib.sha256(path.read_bytes()).hexdigest()


class D22G7SyntheticSQLiteRehearsal(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="iamina-d22-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.a_path = self.root / "amina_vault_v1_native_101.sqlite3"
        self.a = connect_fixture(self.a_path, patient_id=101)
        self.addCleanup(self.a.close)

    def test_additive_and_legacy_70_180_unchanged(self) -> None:
        before = snapshot_legacy(self.a)
        add_sidecar_synthetic_only(self.a)
        self.assertEqual(snapshot_legacy(self.a), before)
        self.assertTrue(table_exists(self.a))
        self.assertEqual(
            self.a.execute(
                "SELECT COUNT(*) FROM glucose_measurement_evidence_v1"
            ).fetchone()[0], 0,
            "No legacy 70/180 evidence may be fabricated",
        )
        self.assertEqual(before[2], 12, "No Drift user_version bump")

    def test_idempotence_without_destructive_rewrite(self) -> None:
        before = snapshot_legacy(self.a)
        add_sidecar_synthetic_only(self.a)
        add_sidecar_synthetic_only(self.a)
        self.assertEqual(before, snapshot_legacy(self.a))
        self.assertEqual(
            self.a.execute(
                "SELECT COUNT(*) FROM glucose_measurement_evidence_v1"
            ).fetchone()[0], 0,
        )

    def test_schema_conflict_fails_closed(self) -> None:
        self.a.execute(
            "CREATE TABLE glucose_measurement_evidence_v1 "
            "(log_entry_id INTEGER PRIMARY KEY)"
        )
        self.a.commit()
        before = snapshot_legacy(self.a)
        with self.assertRaisesRegex(RuntimeError, "Conflicting sidecar"):
            add_sidecar_synthetic_only(self.a)
        self.assertEqual(snapshot_legacy(self.a), before)
        self.assertEqual(
            [x[1] for x in self.a.execute(
                "PRAGMA table_info(glucose_measurement_evidence_v1)"
            )], ["log_entry_id"]
        )

    def test_atomic_failure_rolls_back_creation_and_legacy_is_identical(self) -> None:
        before = snapshot_legacy(self.a)
        with self.assertRaisesRegex(RuntimeError, "injected migration failure"):
            add_sidecar_synthetic_only(self.a, inject_failure=True)
        self.assertFalse(table_exists(self.a))
        self.assertEqual(before, snapshot_legacy(self.a))
        self.assertEqual(self.a.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_explicit_new_manual_metadata_preserves_original(self) -> None:
        add_sidecar_synthetic_only(self.a)
        self.a.execute(
            "INSERT INTO log_entries(blood_sugar, client_uuid) VALUES (?, ?)",
            (7.83 * PHYSICAL_CONVERSION_CANDIDATE, "synthetic-new-101"),
        )
        new_id = self.a.execute(
            "SELECT id FROM log_entries WHERE client_uuid='synthetic-new-101'"
        ).fetchone()[0]
        write_new_synthetic_evidence(
            self.a, log_id=new_id, raw_value=7.83, declared_unit="mmol/L"
        )
        self.a.commit()
        row = self.a.execute(
            "SELECT original_source_value, original_source_unit_ucum, "
            "unit_system, provenance FROM glucose_measurement_evidence_v1 "
            "WHERE log_entry_id=?", (new_id,)
        ).fetchone()
        self.assertEqual(
            row, (7.83, "mmol/L", "http://unitsofmeasure.org", "user_entered")
        )
        self.assertEqual(self.a.execute(
            "SELECT COUNT(*) FROM glucose_measurement_evidence_v1 "
            "WHERE log_entry_id IN (1,2)"
        ).fetchone()[0], 0, "Historic rows must remain UNCLASSIFIED")

    def test_invalid_units_values_duplicates_and_foreign_keys_fail(self) -> None:
        add_sidecar_synthetic_only(self.a)
        for code in ("mgdl", "MMOL/L", "", "g/L"):
            with self.assertRaises(ValueError):
                write_new_synthetic_evidence(
                    self.a, log_id=1, raw_value=7.8, declared_unit=code
                )
        for raw in (0, -7, float("inf"), float("nan"), 1e308):
            with self.assertRaises(ValueError):
                write_new_synthetic_evidence(
                    self.a, log_id=1, raw_value=raw, declared_unit="mmol/L"
                )
        with self.assertRaises(sqlite3.IntegrityError):
            write_new_synthetic_evidence(
                self.a, log_id=9999, raw_value=7.8, declared_unit="mmol/L"
            )
        write_new_synthetic_evidence(
            self.a, log_id=1, raw_value=7.8, declared_unit="mmol/L"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            write_new_synthetic_evidence(
                self.a, log_id=1, raw_value=8.0, declared_unit="mmol/L"
            )
        self.a.rollback()

    def test_patient_a_and_b_are_separate_physical_vaults(self) -> None:
        b_path = self.root / "amina_vault_v1_native_202.sqlite3"
        with connect_fixture(b_path, patient_id=202) as b:
            original_b = snapshot_legacy(b)
            add_sidecar_synthetic_only(self.a)
            write_new_synthetic_evidence(
                self.a, log_id=1, raw_value=140, declared_unit="mg/dL"
            )
            self.a.commit()
            self.assertEqual(snapshot_legacy(b), original_b)
            self.assertFalse(table_exists(b))
            self.assertEqual(self.a.execute(
                "SELECT COUNT(*) FROM glucose_measurement_evidence_v1"
            ).fetchone()[0], 1)
        # This only demonstrates separate files: NOT auth/logout/consent FUE.

    def test_backup_sha256_restore_exact_legacy_and_rollback(self) -> None:
        before = snapshot_legacy(self.a)
        backup_path = self.root / "synthetic-v12-backup.sqlite3"
        digest = backup_snapshot(self.a, backup_path)
        self.assertEqual(len(digest), 64)
        add_sidecar_synthetic_only(self.a)
        self.assertTrue(table_exists(self.a))
        restored_path = self.root / "synthetic-v12-restored.sqlite3"
        shutil.copyfile(backup_path, restored_path)
        self.assertEqual(
            hashlib.sha256(restored_path.read_bytes()).hexdigest(), digest
        )
        with sqlite3.connect(restored_path) as restored:
            self.assertEqual(snapshot_legacy(restored), before)
            self.assertFalse(table_exists(restored))
            self.assertEqual(
                restored.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )

    def test_no_guessing_of_source_unit_or_legacy_target(self) -> None:
        add_sidecar_synthetic_only(self.a)
        target = self.a.execute(
            "SELECT target_range_low, target_range_high, unit_preference "
            "FROM patient_profiles WHERE user_id=101"
        ).fetchone()
        self.assertEqual(target, (70.0, 180.0, "mg/dL"))
        self.assertEqual(
            self.a.execute(
                "SELECT COUNT(*) FROM glucose_measurement_evidence_v1"
            ).fetchone()[0], 0,
        )
        # A legacy display preference, target default, or 70/180 value
        # confers NO claim about original source units or target approval.
