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

# Prototype-only provenance watermark. The watermark freezes the highest ID
# existing when the sidecar is first added; older IDs remain ineligible.
# AUTOINCREMENT in this disposable fixture prevents normal reuse of old IDs.
# This is NOT an authorization boundary against writers with arbitrary SQL.
LEGACY_GUARD_SQL = """
CREATE TABLE glucose_evidence_legacy_guard_v1 (
  singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
  legacy_max_log_id INTEGER NOT NULL CHECK (legacy_max_log_id >= 0)
)
"""

ANTI_LEGACY_TRIGGER_SQL = """
CREATE TRIGGER glucose_evidence_no_legacy_insert_v1
BEFORE INSERT ON glucose_measurement_evidence_v1
FOR EACH ROW
WHEN (SELECT COUNT(*) FROM glucose_evidence_legacy_guard_v1
      WHERE singleton = 1) != 1
  OR NEW.log_entry_id <= (SELECT legacy_max_log_id
                           FROM glucose_evidence_legacy_guard_v1
                           WHERE singleton = 1)
BEGIN
  SELECT RAISE(ABORT, 'legacy provenance attribution forbidden');
END
"""

IMMUTABLE_EVIDENCE_TRIGGER_SQL = """
CREATE TRIGGER glucose_evidence_no_update_v1
BEFORE UPDATE ON glucose_measurement_evidence_v1
FOR EACH ROW
BEGIN
  SELECT RAISE(ABORT, 'source provenance is immutable');
END
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
        canonical = lambda sql: "".join(sql.lower().split()).rstrip(";")
        guard_ddl = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' "
            "AND name='glucose_evidence_legacy_guard_v1'"
        ).fetchone()
        insert_trigger = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='trigger' "
            "AND name='glucose_evidence_no_legacy_insert_v1'"
        ).fetchone()
        immutable_trigger = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='trigger' "
            "AND name='glucose_evidence_no_update_v1'"
        ).fetchone()
        if existing:
            if (canonical(existing[0]) != canonical(EVIDENCE_SQL)
                or guard_ddl is None
                or canonical(guard_ddl[0]) != canonical(LEGACY_GUARD_SQL)
                or insert_trigger is None
                or canonical(insert_trigger[0]) != canonical(ANTI_LEGACY_TRIGGER_SQL)
                or immutable_trigger is None
                or canonical(immutable_trigger[0]) != canonical(IMMUTABLE_EVIDENCE_TRIGGER_SQL)):
                raise RuntimeError("Conflicting sidecar schema; fail closed")
            guard_rows = conn.execute(
                "SELECT legacy_max_log_id FROM glucose_evidence_legacy_guard_v1 "
                "WHERE singleton=1"
            ).fetchall()
            if len(guard_rows) != 1:
                raise RuntimeError("Missing legacy watermark; fail closed")
        else:
            if guard_ddl or insert_trigger or immutable_trigger:
                raise RuntimeError("Partial legacy guard schema; fail closed")
            conn.execute(LEGACY_GUARD_SQL)
            conn.execute(
                "INSERT INTO glucose_evidence_legacy_guard_v1 "
                "(singleton, legacy_max_log_id) "
                "SELECT 1, COALESCE(MAX(id), 0) FROM log_entries"
            )
            conn.execute(EVIDENCE_SQL)
            conn.execute(ANTI_LEGACY_TRIGGER_SQL)
            conn.execute(IMMUTABLE_EVIDENCE_TRIGGER_SQL)
        if inject_failure:
            raise RuntimeError("Synthetic injected migration failure")
        conn.commit()
    except BaseException:
        conn.rollback()
        raise


def append_new_synthetic_measure(
    conn: sqlite3.Connection, *,
    raw_value: float, declared_unit: str, client_uuid: str
) -> int:
    """Atomically append a NEW synthetic log and evidence; no legacy id API.

    Neither caller nor code can supply an existing log ID. A failed evidence
    insert cannot leave a newly created reading without its source record.
    This is NOT authentication or permission for real patient writes.
    """
    if declared_unit not in ("mg/dL", "mmol/L"):
        raise ValueError("Source unit must be explicit UCUM mg/dL or mmol/L")
    if not math.isfinite(raw_value) or raw_value <= 0:
        raise ValueError("Source value must be finite and positive")
    canonical = raw_value * (
        PHYSICAL_CONVERSION_CANDIDATE if declared_unit == "mmol/L" else 1
    )
    if not math.isfinite(canonical) or canonical <= 0:
        raise ValueError("Overflow or underflow in canonical projection")
    if not client_uuid.startswith("synthetic-new-"):
        raise ValueError("Synthetic-only client UUID prefix required")

    conn.execute("SAVEPOINT d22_new_source")
    try:
        cursor = conn.execute(
            "INSERT INTO log_entries(blood_sugar, client_uuid) VALUES (?, ?)",
            (canonical, client_uuid),
        )
        new_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO glucose_measurement_evidence_v1 "
            "(log_entry_id, original_source_value, original_source_unit_ucum, "
            "unit_system, provenance, conversion_contract, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_id, raw_value, declared_unit, "http://unitsofmeasure.org",
             "user_entered", "nist_glucose_1801559_v1",
             "2026-11-02T00:00:00Z"),
        )
        conn.execute("RELEASE SAVEPOINT d22_new_source")
        return new_id
    except BaseException:
        conn.execute("ROLLBACK TO SAVEPOINT d22_new_source")
        conn.execute("RELEASE SAVEPOINT d22_new_source")
        raise


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
        new_id = append_new_synthetic_measure(
            self.a, raw_value=7.83, declared_unit="mmol/L",
            client_uuid="synthetic-new-101-1",
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
        self.assertEqual(
            self.a.execute(
                "SELECT blood_sugar FROM log_entries WHERE id=?", (new_id,)
            ).fetchone()[0],
            7.83 * PHYSICAL_CONVERSION_CANDIDATE,
        )
        self.assertEqual(self.a.execute(
            "SELECT COUNT(*) FROM glucose_measurement_evidence_v1 "
            "WHERE log_entry_id IN (1,2)"
        ).fetchone()[0], 0, "Historic rows must remain UNCLASSIFIED")

    def test_invalid_units_values_duplicates_and_foreign_keys_fail(self) -> None:
        add_sidecar_synthetic_only(self.a)
        before = snapshot_legacy(self.a)
        for code in ("mgdl", "MMOL/L", "", "g/L"):
            with self.assertRaises(ValueError):
                append_new_synthetic_measure(
                    self.a, raw_value=7.8, declared_unit=code,
                    client_uuid="synthetic-new-101-invalid",
                )
        for raw in (0, -7, float("inf"), float("nan"), 1e308):
            with self.assertRaises(ValueError):
                append_new_synthetic_measure(
                    self.a, raw_value=raw, declared_unit="mmol/L",
                    client_uuid="synthetic-new-101-invalid",
                )
        with self.assertRaises(ValueError):
            append_new_synthetic_measure(
                self.a, raw_value=7.8, declared_unit="mmol/L",
                client_uuid="legacy-existing-row",
            )
        self.assertEqual(snapshot_legacy(self.a), before)
        new_id = append_new_synthetic_measure(
            self.a, raw_value=7.8, declared_unit="mmol/L",
            client_uuid="synthetic-new-101-valid",
        )
        count_before_duplicate = self.a.execute(
            "SELECT COUNT(*) FROM log_entries"
        ).fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            append_new_synthetic_measure(
                self.a, raw_value=8.0, declared_unit="mmol/L",
                client_uuid="synthetic-new-101-valid",
            )
        self.assertEqual(self.a.execute(
            "SELECT COUNT(*) FROM log_entries"
        ).fetchone()[0], count_before_duplicate)
        with self.assertRaises(sqlite3.IntegrityError):
            self.a.execute(
                "INSERT INTO glucose_measurement_evidence_v1 "
                "(log_entry_id, original_source_value, "
                "original_source_unit_ucum, unit_system, provenance, "
                "conversion_contract, recorded_at_utc) "
                "VALUES (?, 7.8, 'mmol/L', 'http://unitsofmeasure.org', "
                "'user_entered', 'nist_glucose_1801559_v1', 'now')",
                (9999,),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.a.execute(
                "INSERT INTO glucose_measurement_evidence_v1 "
                "(log_entry_id, original_source_value, "
                "original_source_unit_ucum, unit_system, provenance, "
                "conversion_contract, recorded_at_utc) "
                "VALUES (?, 8, 'mmol/L', 'http://unitsofmeasure.org', "
                "'user_entered', 'nist_glucose_1801559_v1', 'now')",
                (new_id,),
            )
        self.assertEqual(self.a.execute(
            "SELECT COUNT(*) FROM glucose_measurement_evidence_v1 "
            "WHERE log_entry_id IN (1,2)"
        ).fetchone()[0], 0)
        self.a.rollback()

    def test_raw_sql_cannot_attach_source_to_preexisting_legacy_ids(self) -> None:
        """Negative test beyond the helper: raw sidecar SQL for legacy is denied."""
        before = snapshot_legacy(self.a)
        add_sidecar_synthetic_only(self.a)
        self.assertEqual(
            self.a.execute(
                "SELECT legacy_max_log_id FROM glucose_evidence_legacy_guard_v1"
            ).fetchone(), (2,)
        )
        for legacy_id in (1, 2):
            with self.assertRaisesRegex(
                sqlite3.IntegrityError, "legacy provenance attribution forbidden"
            ):
                self.a.execute(
                    "INSERT INTO glucose_measurement_evidence_v1 "
                    "(log_entry_id, original_source_value, original_source_unit_ucum, "
                    "unit_system, provenance, conversion_contract, recorded_at_utc) "
                    "VALUES (?, 70, 'mg/dL', 'http://unitsofmeasure.org', "
                    "'user_entered', 'nist_glucose_1801559_v1', 'now')",
                    (legacy_id,),
                )
        self.assertEqual(snapshot_legacy(self.a), before)
        self.assertEqual(self.a.execute(
            "SELECT COUNT(*) FROM glucose_measurement_evidence_v1"
        ).fetchone()[0], 0)

    def test_source_metadata_update_denied_and_guard_missing_fails_closed(self) -> None:
        add_sidecar_synthetic_only(self.a)
        new_id = append_new_synthetic_measure(
            self.a, raw_value=140, declared_unit="mg/dL",
            client_uuid="synthetic-new-101-adversarial",
        )
        self.a.commit()
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "source provenance is immutable"
        ):
            self.a.execute(
                "UPDATE glucose_measurement_evidence_v1 "
                "SET log_entry_id=1 WHERE log_entry_id=?", (new_id,)
            )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "source provenance is immutable"
        ):
            self.a.execute(
                "UPDATE glucose_measurement_evidence_v1 "
                "SET original_source_value=10 WHERE log_entry_id=?", (new_id,)
            )
        self.a.execute("DELETE FROM glucose_evidence_legacy_guard_v1")
        self.a.commit()  # add_sidecar starts an explicit transaction.
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "legacy provenance attribution forbidden"
        ):
            self.a.execute(
                "INSERT INTO glucose_measurement_evidence_v1 "
                "(log_entry_id, original_source_value, original_source_unit_ucum, "
                "unit_system, provenance, conversion_contract, recorded_at_utc) "
                "VALUES (?, 10, 'mg/dL', 'http://unitsofmeasure.org', "
                "'user_entered', 'nist_glucose_1801559_v1', 'now')",
                (new_id + 1,),
            )
        # A failed DML statement can leave an implicit sqlite3 transaction
        # open. The migration preflight explicitly opens BEGIN IMMEDIATE.
        self.a.rollback()
        with self.assertRaisesRegex(RuntimeError, "Missing legacy watermark"):
            add_sidecar_synthetic_only(self.a)

    def test_patient_a_and_b_are_separate_physical_vaults(self) -> None:
        b_path = self.root / "amina_vault_v1_native_202.sqlite3"
        b = connect_fixture(b_path, patient_id=202)
        try:
            original_b = snapshot_legacy(b)
            add_sidecar_synthetic_only(self.a)
            append_new_synthetic_measure(
                self.a, raw_value=140, declared_unit="mg/dL",
                client_uuid="synthetic-new-101-vault",
            )
            self.a.commit()
            self.assertEqual(snapshot_legacy(b), original_b)
            self.assertFalse(table_exists(b))
            self.assertEqual(self.a.execute(
                "SELECT COUNT(*) FROM glucose_measurement_evidence_v1"
            ).fetchone()[0], 1)
            self.assertEqual(self.a.execute(
                "SELECT COUNT(*) FROM glucose_measurement_evidence_v1 "
                "WHERE log_entry_id IN (1,2)"
            ).fetchone()[0], 0)
        finally:
            b.close()
        # Separate files are NOT auth/logout/consent FUE.

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
