from companion.output_guard import guard_narrator_output
from companion.practical_boundary_filter import sanitize_practical_boundary


def test_guard_rejects_model_selected_kitchen_counter_from_live_parity():
    reply = (
        "You noted that you tend to forget your diabetes tracking in the evening after dinner "
        "and you’d like a very simple solution. Here’s a three-box checklist you can keep on "
        "the kitchen counter for that time of day: □ [ ] □ [ ] □ [ ]"
    )
    guarded = guard_narrator_output(
        reply,
        language="en",
        approved_session_context=False,
        mode="practical",
    )
    assert guarded != reply
    assert "kitchen counter" not in guarded.lower()
    assert "empty checklist boxes" in guarded.lower()


def test_guard_rejects_darija_masculine_feminine_mismatch():
    reply = "خليها بسيطة: ثلاث خانات خاويين بلا محتوى مفروض، وعمر غير باللي نتا اخترتي من قبل."
    guarded = guard_narrator_output(
        reply,
        language="ar-MA",
        approved_session_context=False,
        mode="practical",
    )
    assert guarded != reply
    assert "نتا اخترتي" not in guarded
    assert "نتا اخترت" in guarded


def test_guard_rejects_broken_arabic_empathy_from_live_parity():
    reply = "أشعر بكمّك، وأقدّر صعوبة التحمل مع التفكير المتواصل في السكري."
    guarded = guard_narrator_output(
        reply,
        language="ar",
        approved_session_context=False,
        mode="emotional",
    )
    assert guarded != reply
    assert "أشعر بكمّك" not in guarded
    assert "متعب" in guarded


def test_guard_rejects_invented_french_self_reminder_from_live_parity():
    reply = (
        "Voici trois cases simples pour le soir après le dîner. "
        "Tu peux les garder visibles pour te rappeler de ton suivi."
    )
    guarded = guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
        mode="practical",
    )
    assert guarded != reply
    assert "te rappeler" not in guarded.lower()
    assert "cases vides" in guarded.lower()


def test_post_filter_rejects_invented_kuwaiti_tracking_content_from_live_parity():
    reply = (
        "حط لك قالب بسيط فيه ثلاث خانات فاضية تكتب فيها ملاحظاتك أو توقيت المتابعة، "
        "وتعبّيها فقط بالمعلومات اللي تختارها من قبل."
    )
    guarded = sanitize_practical_boundary(reply)
    assert guarded != reply
    assert "ملاحظاتك أو توقيت المتابعة" not in guarded
    assert "حيل" in guarded
    assert "ثلاث خانات فاضية" in guarded


def test_post_filter_rejects_invented_omani_memory_trigger_from_live_parity():
    reply = (
        "ممكن تحط ثلاثة خانات فاضية بدون محتوى محدد الآن، "
        "وتعبّي أي خانة تختارها وقت ما تحس إنك تذكّرت."
    )
    guarded = sanitize_practical_boundary(reply)
    assert guarded != reply
    assert "وقت ما تحس" not in guarded
    assert "واجد" in guarded
    assert "ثلاث خانات فاضية" in guarded


def test_post_filter_rejects_invented_darija_content_from_live_parity():
    reply = "من بعد العشا، دير ثلاث خانات خاويين وتعبّيهم غير ب-«اخترت هاد الشي» ملي كتفطر العشا."
    guarded = sanitize_practical_boundary(reply)
    assert guarded != reply
    assert "اخترت هاد الشي" not in guarded
    assert "كتفطر العشا" not in guarded
    assert "خانات خاويين" in guarded
    assert "نتا اخترت من قبل" in guarded


def test_post_filter_rejects_bad_emirati_empathy_from_live_parity():
    reply = "ترا التفكير بهالشي متعب وايد، وكلنا نحتاج نفكّس شوية."
    guarded = sanitize_practical_boundary(reply)
    assert guarded != reply
    assert "نفكّس شوية" not in guarded
    assert "ترا هالشي متعب وايد" in guarded
    assert "وأنا وياك" in guarded
