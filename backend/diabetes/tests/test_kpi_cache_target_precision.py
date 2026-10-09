"""V1-01 regression: KPI cache ranges must not collapse distinct clinical inputs."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from diabetes.api.v1.kpis import _kpi_cache_key, get_kpis


class KpiCacheRangePrecisionTests(SimpleTestCase):
    def test_fractional_bounds_do_not_alias(self):
        baseline = _kpi_cache_key(17, 21, 70.0, 180.0)
        self.assertNotEqual(baseline, _kpi_cache_key(17, 21, 70.5, 180.0))
        self.assertNotEqual(baseline, _kpi_cache_key(17, 21, 70.0, 180.5))
        self.assertNotEqual(
            _kpi_cache_key(17, 21, 70.1, 180.0),
            _kpi_cache_key(17, 21, 70.9, 180.0),
        )

    def test_equivalent_numeric_inputs_share_key_but_patients_and_periods_do_not(self):
        key = _kpi_cache_key(17, 21, 70, 180)
        self.assertEqual(key, _kpi_cache_key(17, 21, 70.0, 180.0))
        self.assertNotEqual(key, _kpi_cache_key(18, 21, 70.0, 180.0))
        self.assertNotEqual(key, _kpi_cache_key(17, 14, 70.0, 180.0))

    def test_endpoint_recomputes_after_bound_change_within_same_integer_bucket(self):
        """A cached standard-range result must not bypass an altered-range evaluation."""
        request = SimpleNamespace(user=SimpleNamespace(id=17))
        stored = {}
        fields = {
            "avg_glucose": None,
            "std_dev": None,
            "cv_pct": None,
            "tir_pct": None,
            "tar_pct": None,
            "tbr_pct": None,
            "gmi": None,
            "log_count": 0,
            "days_with_data": 0,
            "has_sufficient_data": False,
            "gmi_confidence": None,
            "gmi_basis": "insufficient",
            "gri": None,
            "gri_zone": None,
            "gri_label_fr": None,
        }

        with (
            patch("diabetes.api.v1.kpis.cache") as cache,
            patch("diabetes.api.v1.kpis.compute_kpis") as calculate,
            patch("diabetes.api.v1.kpis.assess_cgm_window") as window,
            patch("diabetes.api.v1.kpis.project_public_kpis", return_value=fields),
        ):
            cache.get.side_effect = stored.get
            cache.set.side_effect = lambda key, value, ttl: stored.__setitem__(key, value)
            window.return_value.verified = False

            get_kpis(request, days=21, target_low=70.0, target_high=180.0)
            get_kpis(request, days=21, target_low=70.5, target_high=180.0)
            self.assertEqual(calculate.call_count, 2)
            self.assertEqual(len(stored), 2)
