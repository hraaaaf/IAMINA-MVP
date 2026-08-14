import pytest

from core.triage_classification import TriageClass, classify


@pytest.mark.parametrize(
    "message",
    [
        "غَادِي نْطِيح",
        "غــــادي نطيح",
        "غادي   نطيح",
        "مَا كَنْشُوفْ وَالُو",
        "ما   كنشوف   والو",
        "فَقَدْتُ الوعي",
        "إِغْمَاء",
    ],
)
def test_arabic_orthographic_noise_preserves_emergency_classification(message):
    assert classify(message) is TriageClass.GLYCEMIC_EMERGENCY


@pytest.mark.parametrize(
    "message",
    [
        "غادي للدار دابا",
        "ما كنشوف التلفاز اليوم",
        "السكر 140",
        "عندي موعد غدا",
    ],
)
def test_arabic_normalization_does_not_expand_unrelated_triage(message):
    assert classify(message) is TriageClass.NONE
