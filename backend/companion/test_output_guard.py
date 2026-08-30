from companion.output_guard import ARABIC_RE, LATIN_RE, guard_narrator_output, safe_fallback


def test_guard_blocks_explicit_behavior_advice_without_approved_context():
    reply = "Essaie de marcher 10 minutes puis bois un verre d'eau."
    guarded = guard_narrator_output(reply, language="fr", approved_session_context=False)
    assert "marcher" not in guarded.lower()
    assert "bois" not in guarded.lower()
    assert "rappel" in guarded.lower()


def test_guard_allows_abstract_organization_copy():
    reply = "Mets un rappel et garde une checklist courte."
    assert guard_narrator_output(reply, language="fr", approved_session_context=False) == reply


def test_guard_does_not_treat_context_presence_as_behavior_authorization():
    reply = "Essaie de marcher 10 minutes."
    guarded = guard_narrator_output(reply, language="fr", approved_session_context=True)
    assert guarded != reply
    assert "rappel" in guarded.lower()


def test_guard_replaces_overlong_week_plan_with_empty_structure():
    reply = " ".join(["organisation"] * 46)
    guarded = guard_narrator_output(reply, language="fr", approved_session_context=False, mode="practical", weekly=True)
    assert "trois cases vides" in guarded
    assert "médecin" not in guarded.lower()


def test_guard_uses_stronger_compression_for_very_long_output():
    medium = guard_narrator_output(" ".join(["organisation"] * 50), language="fr", approved_session_context=False)
    very_long = guard_narrator_output(" ".join(["organisation"] * 70), language="fr", approved_session_context=False)
    assert medium != very_long
    assert "un seul repère" in medium
    assert "Réduis au minimum" in very_long


def test_guard_blocks_model_selected_tracking_content():
    guarded = guard_narrator_output("Note 1 point sur ton humeur chaque lundi.", language="fr", approved_session_context=False)
    assert "humeur" not in guarded.lower()
    assert "rappel" in guarded.lower()


def test_guard_blocks_model_selected_daily_frequency():
    reply = "Aujourd’hui j’ai noté mon suivi et coché la case du jour précédent."
    guarded = guard_narrator_output(reply, language="fr", approved_session_context=False)
    assert guarded != reply
    assert "jour précédent" not in guarded.lower()
    assert "rappel" in guarded.lower()


def test_guard_reframes_clinician_tracking_question_without_selecting_content():
    reply = (
        "Prépare ces 4 questions :\n"
        "- Quelles informations voulez-vous que je note ?\n"
        "- Quels changements dois-je vous signaler ?\n"
        "- Quels critères utilisez-vous pour réévaluer mon traitement ?\n"
        "- Quand dois-je vous recontacter ?"
    )
    guarded = guard_narrator_output(reply, language="fr", approved_session_context=False, mode="clinician_prep")
    assert "apporter" in guarded.lower()
    assert "que je note" not in guarded.lower()
    assert guarded.count("?") == 4


def test_guard_blocks_arabizi_content_selection():
    guarded = guard_narrator_output("Sji mood dyalk f checklist.", language="ar-MA", approved_session_context=False, prefer_latin_script=True)
    assert "mood" not in guarded.lower()
    assert "reminder" in guarded.lower()


def test_guard_bounds_emotional_shape():
    reply = "\n".join(("Première phrase empathique.", "Deuxième ligne avec un plan."))
    guarded = guard_narrator_output(reply, language="fr", approved_session_context=False, mode="emotional")
    assert "plan" not in guarded.lower()
    assert "moment" in guarded.lower()


def test_guard_replaces_arabic_contamination_after_latin_darija_input():
    reply = "Khlliha minimal bla contenu مفروض."
    guarded = guard_narrator_output(reply, language="ar-MA", approved_session_context=False, prefer_latin_script=True)
    assert guarded != reply
    assert not ARABIC_RE.search(guarded)


def test_guard_replaces_latin_darija_after_arabic_script_input():
    reply = "Kanbghik tkhalli l'kalam f'khouk, w kanfham l'ma9la3 dyalk."
    guarded = guard_narrator_output(reply, language="ar-MA", approved_session_context=False, mode="emotional")
    assert guarded != reply
    assert ARABIC_RE.search(guarded)
    assert not LATIN_RE.search(guarded)


def test_guard_replaces_french_contamination_after_arabic_script_input():
    reply = "Voici 3 questions: شنو نجيب؟ شنو نقول؟ وإمتى نرجع؟"
    guarded = guard_narrator_output(reply, language="ar-MA", approved_session_context=False, mode="clinician_prep")
    assert guarded != reply
    assert ARABIC_RE.search(guarded)
    assert not LATIN_RE.search(guarded)
    assert guarded.count("؟") == 4


def test_all_latin_darija_fallbacks_are_script_clean():
    for mode in ("practical", "emotional", "clinician_prep"):
        for weekly in (False, True):
            for very_long in (False, True):
                fallback = safe_fallback("ar-MA", mode=mode, weekly=weekly, very_long=very_long, prefer_latin_script=True)
                assert not ARABIC_RE.search(fallback)


def test_all_arabic_darija_fallbacks_are_script_clean():
    for mode in ("practical", "emotional", "clinician_prep"):
        for weekly in (False, True):
            for very_long in (False, True):
                fallback = safe_fallback("ar-MA", mode=mode, weekly=weekly, very_long=very_long, prefer_latin_script=False)
                assert ARABIC_RE.search(fallback)
                assert not LATIN_RE.search(fallback)


def test_guard_replaces_arabic_therapeutic_clinician_questions():
    reply = (
        "هادي أسئلة للطبيب:\n"
        "- شحال الجرعة المناسبة ديال الإنسولين؟\n"
        "- واش نزيد الجرعة؟\n"
        "- إمتى نبدل العلاج؟\n"
        "- إمتى نرجع عندك؟"
    )
    guarded = guard_narrator_output(reply, language="ar-MA", approved_session_context=False, mode="clinician_prep")
    assert guarded != reply
    assert "شحال الجرعة" not in guarded
    assert guarded.count("؟") == 4


def test_guard_replaces_english_therapeutic_clinician_questions():
    reply = "What insulin dose should I take? Should I increase it? What treatment should change? When should I call you?"
    guarded = guard_narrator_output(reply, language="en", approved_session_context=False, mode="clinician_prep")
    assert guarded != reply
    assert "What insulin dose" not in guarded
    assert guarded.count("?") == 4


def test_guard_rejects_arabic_glucose_measurement_schedule_from_live_probe():
    reply = "ضبط تنبيه هاتفك بعد 30-45 دقيقة من العشاء ثم قياس السكر وتسجيل النتيجة."
    guarded = guard_narrator_output(reply, language="ar", approved_session_context=False)
    assert guarded != reply
    assert "قياس السكر" not in guarded


def test_guard_rejects_arabic_selected_tracking_frequency_from_live_probe():
    reply = "حدد توقيت ثابت كل 3 أيام لتسجيل مستوى السكر ثم راجع الملاحظات أسبوعياً."
    guarded = guard_narrator_output(reply, language="ar-SA", approved_session_context=False)
    assert guarded != reply
    assert "تسجيل مستوى السكر" not in guarded


def test_guard_rejects_specific_schedule_selection_without_health_content():
    reply = "- Après le dîner\n- Avant de me coucher\n- Début de la semaine (ex. lundi)"
    guarded = guard_narrator_output(reply, language="fr", approved_session_context=False)
    assert guarded != reply
    assert "lundi" not in guarded.lower()


def test_guard_rejects_therapeutic_recap_in_english():
    reply = "We’ll prepare questions for your doctor about insulin dosing and related concerns."
    guarded = guard_narrator_output(reply, language="en", approved_session_context=False)
    assert guarded != reply
    assert "insulin" not in guarded.lower()


def test_guard_rejects_therapeutic_recap_in_arabic():
    reply = "حضّرت لك أسئلة للطبيب بخصوص قراءات السكري وتعديل جرعة الأنسولين."
    guarded = guard_narrator_output(reply, language="ar-SA", approved_session_context=False)
    assert guarded != reply
    assert "جرعة" not in guarded
    assert "الأنسولين" not in guarded
