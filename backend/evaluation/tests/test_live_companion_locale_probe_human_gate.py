from evaluation.live_companion_locale_probe import (
    _TECHNICAL_FAILURE_PATTERN,
    _contains_evening_anchor,
    _has_target_gulf_dialect,
)


def test_darija_generic_min_baad_is_not_an_evening_anchor():
    assert not _contains_evening_anchor("ar-MA", "من بعد شي أيام كننسى")
    assert _contains_evening_anchor("ar-MA", "بالليل من بعد العشا كننسى")


def test_visible_technical_failure_is_machine_detectable():
    assert _TECHNICAL_FAILURE_PATTERN.search(
        "Temporary technical issue. Please try again shortly."
    )


def test_gulf_dialect_marker_rejects_generic_msa_and_accepts_target_copy():
    generic = "حضّر هذه الأسئلة الأربعة: ما المعلومات التي يجب أن أحضرها؟"
    assert not _has_target_gulf_dialect("ar-KW", generic)
    assert _has_target_gulf_dialect("ar-KW", "شنو المعلومات اللي أجيبها؟")
    assert _has_target_gulf_dialect("ar-AE", "شو المعلومات اللي أجيبها؟")
    assert _has_target_gulf_dialect("ar-OM", "وش المعلومات اللي أجيبها؟")
