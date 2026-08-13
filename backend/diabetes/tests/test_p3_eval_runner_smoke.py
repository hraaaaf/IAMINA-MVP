from django.test import SimpleTestCase


class EvalRunnerSmokeTests(SimpleTestCase):
    def test_all_required_flags_must_pass(self):
        flags = (True, True, True, True)
        self.assertTrue(all(flags))

    def test_one_failed_flag_blocks(self):
        flags = (True, True, False, True)
        self.assertFalse(all(flags))
