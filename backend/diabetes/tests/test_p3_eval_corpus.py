from django.test import SimpleTestCase

from diabetes.evals.corpus import CORPUS, CorpusEntry, validate_corpus


class EvalCorpusTests(SimpleTestCase):
    def test_default(self):
        validate_corpus()
        self.assertEqual(len(CORPUS), 4)

    def test_indices(self):
        self.assertTrue(all(0 <= item.suite_index < 12 for item in CORPUS))

    def test_duplicate(self):
        items = (
            CorpusEntry("A", "L", 0),
            CorpusEntry("A", "N", 1),
            CorpusEntry("C", "F", 2),
            CorpusEntry("D", "B", 3),
        )
        with self.assertRaises(ValueError):
            validate_corpus(items)
