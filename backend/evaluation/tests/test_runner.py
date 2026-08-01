from evaluation.dataset import validated_cases
from evaluation.runner import run_dataset


class StaticAdapter:
    name = "static-eval"

    def invoke(self, case):
        return {"case_id": case.case_id, "accepted": True}


def test_runner_records_provider_latency_and_dataset_fingerprint():
    cases = validated_cases()[:2]
    runs = run_dataset(StaticAdapter(), cases)
    assert len(runs) == 2
    assert all(run.provider == "static-eval" for run in runs)
    assert all(run.latency_ms >= 0 for run in runs)
    assert [run.dataset_fingerprint for run in runs] == [case.fingerprint for case in cases]
