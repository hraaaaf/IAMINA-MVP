"""
ATTD/Battelino 5-zone KPI breakdown — invariants & coherence.

The doctor_brief PDF displays TBR2/TBR1/TIR/TAR1/TAR2 separately. Each must
match the aggregate equivalents exposed for the patient-facing dashboard,
otherwise the PDF tells the clinician a different story than the app tells
the patient.

Tolerance is 1.5 percentage points to absorb the per-zone SQL ROUND(., 1).
"""
from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.test import TestCase

from diabetes.models import LogEntry
from diabetes.services.clinical.sql_analytics import compute_kpis


def _mkuser(name: str) -> User:
    return User.objects.create_user(username=name, password="x")


def _seed(user: User, values_and_sources):
    """values_and_sources: list of (blood_sugar, source)."""
    now = datetime.now(timezone.utc)
    for i, (val, src) in enumerate(values_and_sources):
        LogEntry.objects.create(
            patient=user,
            blood_sugar=val,
            source=src,
            logged_at=now - timedelta(hours=i),
        )


class FiveZoneInvariantTest(TestCase):

    def test_tbr_levels_sum_to_aggregate(self):
        user = _mkuser("sum_tbr")
        _seed(user, [
            (40, "manual"),   # TBR2 (<54)
            (45, "manual"),   # TBR2
            (60, "manual"),   # TBR1 (54-69)
            (65, "manual"),   # TBR1
            (120, "manual"),  # TIR
            (200, "manual"),  # TAR1
            (260, "manual"),  # TAR2
        ])
        kpis = compute_kpis(patient_id=user.id, days=7)
        self.assertIsNotNone(kpis.tbr_level1_pct)
        self.assertIsNotNone(kpis.tbr_level2_pct)
        combined = (kpis.tbr_level1_pct or 0) + (kpis.tbr_level2_pct or 0)
        self.assertAlmostEqual(combined, kpis.tbr_pct or 0, delta=1.5)

    def test_tar_levels_sum_to_aggregate(self):
        user = _mkuser("sum_tar")
        _seed(user, [
            (40, "manual"),
            (120, "manual"),
            (190, "manual"),  # TAR1
            (220, "manual"),  # TAR1
            (260, "manual"),  # TAR2
            (320, "manual"),  # TAR2
            (140, "manual"),
        ])
        kpis = compute_kpis(patient_id=user.id, days=7)
        self.assertIsNotNone(kpis.tar_level1_pct)
        self.assertIsNotNone(kpis.tar_level2_pct)
        combined = (kpis.tar_level1_pct or 0) + (kpis.tar_level2_pct or 0)
        self.assertAlmostEqual(combined, kpis.tar_pct or 0, delta=1.5)

    def test_five_zones_sum_to_100(self):
        user = _mkuser("sum_all")
        _seed(user, [
            (40, "manual"), (45, "manual"),    # TBR2
            (60, "manual"),                    # TBR1
            (90, "manual"), (120, "manual"),   # TIR
            (160, "manual"), (180, "manual"),  # TIR
            (200, "manual"),                   # TAR1
            (260, "manual"), (300, "manual"),  # TAR2
        ])
        kpis = compute_kpis(patient_id=user.id, days=7)
        total = (
            (kpis.tbr_level2_pct or 0)
            + (kpis.tbr_level1_pct or 0)
            + (kpis.tir_pct or 0)
            + (kpis.tar_level1_pct or 0)
            + (kpis.tar_level2_pct or 0)
        )
        self.assertAlmostEqual(total, 100.0, delta=1.5)


class TbrLevel1ExclusiveTest(TestCase):
    """TBR1 covers 54-69 mg/dL exclusively. 54 belongs to TBR1, 53 to TBR2."""

    def test_boundary_54_is_tbr1_not_tbr2(self):
        user = _mkuser("boundary_54")
        _seed(user, [(54, "manual"), (54, "manual"), (54, "manual"), (54, "manual"), (54, "manual")])
        kpis = compute_kpis(patient_id=user.id, days=7)
        self.assertEqual(kpis.tbr_level1_pct, 100.0)
        self.assertEqual(kpis.tbr_level2_pct, 0.0)

    def test_boundary_53_is_tbr2_not_tbr1(self):
        user = _mkuser("boundary_53")
        _seed(user, [(53, "manual"), (53, "manual"), (53, "manual"), (53, "manual"), (53, "manual")])
        kpis = compute_kpis(patient_id=user.id, days=7)
        self.assertEqual(kpis.tbr_level2_pct, 100.0)
        self.assertEqual(kpis.tbr_level1_pct, 0.0)


class TarLevel1ExclusiveTest(TestCase):
    """TAR1 covers 181-250 mg/dL. 250 belongs to TAR1, 251 to TAR2."""

    def test_boundary_250_is_tar1_not_tar2(self):
        user = _mkuser("boundary_250")
        _seed(user, [(250, "manual"), (250, "manual"), (250, "manual"), (250, "manual"), (250, "manual")])
        kpis = compute_kpis(patient_id=user.id, days=7)
        self.assertEqual(kpis.tar_level1_pct, 100.0)
        self.assertEqual(kpis.tar_level2_pct, 0.0)

    def test_boundary_251_is_tar2_not_tar1(self):
        user = _mkuser("boundary_251")
        _seed(user, [(251, "manual"), (251, "manual"), (251, "manual"), (251, "manual"), (251, "manual")])
        kpis = compute_kpis(patient_id=user.id, days=7)
        self.assertEqual(kpis.tar_level2_pct, 100.0)
        self.assertEqual(kpis.tar_level1_pct, 0.0)


class CgmActivePctTest(TestCase):

    def test_all_cgm_is_100pct(self):
        user = _mkuser("all_cgm")
        _seed(user, [(120, "cgm")] * 5)
        kpis = compute_kpis(patient_id=user.id, days=7)
        self.assertEqual(kpis.cgm_active_pct, 100.0)

    def test_no_cgm_is_0pct(self):
        user = _mkuser("no_cgm")
        _seed(user, [(120, "manual")] * 5)
        kpis = compute_kpis(patient_id=user.id, days=7)
        self.assertEqual(kpis.cgm_active_pct, 0.0)

    def test_mixed_cgm_smbg(self):
        user = _mkuser("mixed_cgm")
        _seed(user, [
            (120, "cgm"), (130, "cgm"), (140, "cgm"),
            (150, "manual"), (160, "manual"),
        ])
        kpis = compute_kpis(patient_id=user.id, days=7)
        # 3/5 = 60%
        self.assertAlmostEqual(kpis.cgm_active_pct or 0, 60.0, delta=0.5)
