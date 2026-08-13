from django.test import SimpleTestCase

from diabetes.evals.cases import EvalCase, validate_cases


class EvalCaseTests(SimpleTestCase):
    def test_ok(self):
        validate_cases((EvalCase("A", "one", True), EvalCase("B", "two", False)))

    def test_same_id(self):
        with self.assertRaises(ValueError):
            validate_cases((EvalCase("A", "one", True), EvalCase("A", "two", False)))

    def test_blank_dimension(self):
        with self.assertRaises(ValueError):
            validate_cases((EvalCase("A", " ", True),))
