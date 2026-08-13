from django.test import SimpleTestCase

from diabetes.evals.summary import summarize


class EvalSummaryTests(SimpleTestCase):
    def test_all_true(self):
        self.assertEqual(
            summarize((True, True, True)),
            {"count": 3, "ok": 3, "error": 0, "ratio": 1.0},
        )

    def test_mixed(self):
        self.assertEqual(
            summarize((True, False, True, False)),
            {"count": 4, "ok": 2, "error": 2, "ratio": 0.5},
        )

    def test_empty(self):
        self.assertEqual(
            summarize(()),
            {"count": 0, "ok": 0, "error": 0, "ratio": 1.0},
        )
