from companion.output_guard import guard_narrator_output


def test_guard_blocks_explicit_behavior_advice_without_approved_context():
    reply = "Essaie de marcher 10 minutes puis bois un verre d'eau."
    guarded = guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
    )
    assert "marcher" not in guarded.lower()
    assert "bois" not in guarded.lower()
    assert "rappel" in guarded.lower()


def test_guard_allows_organization_of_recorded_health_topics():
    reply = "Note tes glycémies, ton alimentation et ton humeur dans la même liste."
    assert guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
    ) == reply


def test_guard_preserves_reply_with_approved_context():
    reply = "Essaie de marcher 10 minutes."
    assert guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=True,
    ) == reply


def test_guard_replaces_overlong_week_plan():
    reply = " ".join(["organisation"] * 46)
    guarded = guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
        weekly=True,
    )
    assert "Cette semaine" in guarded
    assert "trois cases" in guarded


def test_guard_replaces_overlong_clinician_prep_with_four_questions():
    reply = " ".join(["question"] * 81) + " ? ?"
    guarded = guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
        mode="clinician_prep",
    )
    assert guarded.count("?") == 4
    assert "réévaluer mon traitement" in guarded


def test_guard_keeps_emotional_reply_to_one_line():
    reply = "Je comprends.\nVoici un plan avec plusieurs étapes à faire cette semaine."
    guarded = guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
        mode="emotional",
    )
    assert "plan" not in guarded.lower()
    assert "\n" not in guarded


def test_guard_keeps_latin_darija_fallback_script():
    reply = " ".join(["routine"] * 50)
    guarded = guard_narrator_output(
        reply,
        language="ar-MA",
        approved_session_context=False,
        weekly=True,
        prefer_latin_script=True,
    )
    assert "reminder" in guarded.lower()
    assert not any("\u0600" <= char <= "\u06ff" for char in guarded)
