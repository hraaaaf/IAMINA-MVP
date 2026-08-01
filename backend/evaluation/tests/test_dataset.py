from evaluation.contracts import Locale, Modality, Severity
from evaluation.dataset import validated_cases


def test_dataset_is_valid_unique_and_fingerprinted():
    cases = validated_cases()
    assert len(cases) >= 7
    assert len({case.case_id for case in cases}) == len(cases)
    assert all(len(case.fingerprint) == 64 for case in cases)


def test_dataset_covers_every_required_modality():
    modalities = {case.modality for case in validated_cases()}
    assert modalities == set(Modality)


def test_dataset_covers_baseline_and_mena_locales():
    locales = {case.locale for case in validated_cases()}
    assert {Locale.FR, Locale.EN, Locale.AR, Locale.AR_MA, Locale.AR_MA_LATN, Locale.MIXED} <= locales


def test_high_severity_cases_exist_for_text_and_stt():
    pairs = {
        (case.modality, case.severity)
        for case in validated_cases()
    }
    assert (Modality.TEXT, Severity.HIGH) in pairs
    assert (Modality.STT, Severity.HIGH) in pairs


def test_all_cases_are_synthetic_and_minimized():
    assert all(case.synthetic and case.minimized for case in validated_cases())
