import inspect

from django.test import SimpleTestCase

from diabetes.services.clinical import evidence_horizon_review as review


class HorizonReviewContractTests(SimpleTestCase):
    def test_comparison_is_limited_to_source_records(self):
        source = inspect.getsource(review.compare_candidate)
        self.assertIn("record.kind == RecordKind.SOURCE", source)

    def test_relation_vocabulary_is_bounded(self):
        self.assertEqual(
            {item.value for item in review.HorizonRelation},
            {
                "identifier_match",
                "possible_successor",
                "topic_overlap",
                "new_candidate",
            },
        )

    def test_review_readiness_reuses_candidate_gate(self):
        source = inspect.getsource(review.compare_candidate)
        self.assertIn("candidate.eligible_for_registry_review", source)

    def test_module_exposes_no_registry_write_function(self):
        public_names = {name for name in vars(review) if not name.startswith("_")}
        self.assertFalse(public_names & {"save", "create", "update", "delete", "promote"})
