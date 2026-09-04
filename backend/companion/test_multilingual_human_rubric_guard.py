from types import SimpleNamespace

import pytest

from companion import conversation
from companion.output_guard import guard_narrator_output, safe_fallback


def test_darija_evening_anchor_does_not_treat_generic_min_baad_as_evening():
    assert not conversation._contains_evening_anchor("ar-MA", "من بعد شي أيام كننسى")
    assert conversation._contains_evening_anchor("ar-MA", "بالليل من بعد العشا كننسى")


def test_practical_continuity_retries_when_reply_invents_evening(monkeypatch):
    monkeypatch.setattr(conversation, "_is_verbatim_repeat", lambda *args, **kwargs: False)
    assert conversation._needs_continuity_retry(
        "بالليل من بعد العشا، خليها بسيطة بزاف.",
        "كنلقى صعوبة نبقى منتظم فمتابعة السكري، من بعد شي أيام كننسى.",
        patient=object(),
        mode="practical",
        language="ar-MA",
    )


@pytest.mark.parametrize(
    ("language", "message", "marker"),
    [
        ("ar-SA", "إذا كانت قراءاتي مرتفعة، كم وحدة إنسولين آخذ؟", "ما أقدر"),
        ("ar-AE", "إذا كانت قراءاتي مرتفعة، كم وحدة إنسولين آخذ؟", "ما أقدر"),
        ("ar-KW", "إذا كانت قراءاتي مرتفعة، جم وحدة إنسولين آخذ؟", "ما أقدر"),
        ("ar-QA", "إذا كانت قراءاتي مرتفعة، كم وحدة إنسولين آخذ؟", "ما أقدر"),
        ("ar-OM", "إذا كانت قراءاتي مرتفعة، كم وحدة إنسولين آخذ؟", "ما أقدر"),
    ],
)
def test_gulf_dose_boundary_stays_colloquial_and_safe(language, message, marker):
    reply = conversation._safety_reply(message, patient=None, language=language)
    assert reply is not None
    assert marker in reply
    assert "جرعة الإنسولين" in reply
    assert "أساعدك" in reply


def test_guard_replaces_visible_technical_failure_with_practical_help():
    guarded = guard_narrator_output(
        "Temporary technical issue. Please try again shortly.",
        language="en",
        approved_session_context=False,
        mode="practical",
    )
    assert "technical issue" not in guarded.lower()
    assert "empty checklist boxes" in guarded.lower()
    assert "reminder" not in guarded.lower()
    assert "fixed time" not in guarded.lower()


def test_guard_replaces_question_only_darija_practical_reply():
    guarded = guard_narrator_output(
        "شنو الوقت اللي كتفضّل؟ واش كتستعمل شي وسيلة تنبيه؟",
        language="ar-MA",
        approved_session_context=False,
        mode="practical",
    )
    assert "؟" not in guarded
    assert "خانات خاويين" in guarded
    assert "تذكير" not in guarded


def test_guard_replaces_bad_darija_emotional_wording():
    guarded = guard_narrator_output(
        "كنتفهم أن التفكير المستمر في السكري يقدر يكون مرهق ومقنّع لك.",
        language="ar-MA",
        approved_session_context=False,
        mode="emotional",
    )
    assert "مقنّع" not in guarded
    assert "عياك" in guarded


@pytest.mark.parametrize(
    ("language", "marker"),
    [
        ("ar-SA", "خلّها"),
        ("ar-AE", "وايد"),
        ("ar-KW", "حيل"),
        ("ar-QA", "وايد"),
        ("ar-OM", "واجد"),
    ],
)
def test_gulf_practical_fallback_is_locale_colloquial(language, marker):
    assert marker in safe_fallback(language, mode="practical")


def test_saudi_emotional_fallback_is_locale_colloquial():
    generic_msa = "أفهمك، كثرة التفكير بالسكري كل يوم متعبة فعلًا."
    guarded = guard_narrator_output(
        generic_msa,
        language="ar-SA",
        approved_session_context=False,
        mode="emotional",
    )
    assert guarded != generic_msa
    assert "هالمشكلة" in guarded
    assert guarded.count(".") <= 1


def test_guard_rejects_mixed_msa_darija_recap_wording():
    mixed = "توعدنا نخلي ملاحظة بسيطة بالليل بعد العشاء، بثلاث خانات فارغة، وحضرنا أسئلة للطبيب."
    guarded = guard_narrator_output(
        mixed,
        language="ar-MA",
        approved_session_context=False,
        mode="recap",
    )
    assert guarded != mixed
    assert "توعدنا" not in guarded
    assert "خانات فارغة" not in guarded


def test_qatari_recap_health_tracking_selection_is_rejected():
    reply = (
        "اتفقنا إنك تسجّل ملاحظات بسيطة بعد العشا وتجهّز أربع أسئلة للطبيب "
        "عن قراءات السكر، التغيّرات المطلوبة، معايير إعادة التقييم ومتى تتواصل معه."
    )
    guarded = guard_narrator_output(
        reply,
        language="ar-QA",
        approved_session_context=False,
        mode="recap",
    )
    assert guarded != reply
    assert "قراءات السكر" not in guarded


def test_guard_rejects_english_practical_summary_without_mechanism():
    reply = (
        "You’ve shared that keeping up with diabetes tracking feels hard, and that "
        "the routine tends to fade after a few days."
    )
    guarded = guard_narrator_output(
        reply,
        language="en",
        approved_session_context=False,
        mode="practical",
    )
    assert guarded != reply
    assert "empty checklist boxes" in guarded.lower()


def test_guard_rejects_arabic_practical_summary_without_mechanism():
    reply = "متابعة السكري صعبة وتنسى بعد بضعة أيام، وهذا يعكس صعوبة الاستمرار."
    guarded = guard_narrator_output(
        reply,
        language="ar",
        approved_session_context=False,
        mode="practical",
    )
    assert guarded != reply
    assert "خانات فارغة" in guarded


def test_guard_rejects_french_glucose_checklist_from_live_parity():
    reply = (
        "Voici une checklist simple après le dîner :\n"
        "- J’ai vérifié ma glycémie\n"
        "- J’ai noté le résultat\n"
        "- J’ai rangé le matériel"
    )
    guarded = guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
        mode="practical",
    )
    assert guarded != reply
    assert "glycémie" not in guarded.lower()
    assert "cases vides" in guarded.lower()


def test_guard_rejects_arabic_reminder_inflection_from_live_parity():
    reply = "ثلاثة خانات فاضية تذكّرك بمتابعة السكري، وحطّها بمكان تشوفه عقب العشا."
    guarded = guard_narrator_output(
        reply,
        language="ar-AE",
        approved_session_context=False,
        mode="practical",
    )
    assert guarded != reply
    assert "تذكّرك" not in guarded
    assert "وايد" in guarded
