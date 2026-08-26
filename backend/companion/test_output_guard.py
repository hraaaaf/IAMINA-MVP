from companion.output_guard import guard_unapproved_behavior


def test_guard_blocks_explicit_behavior_advice_without_approved_context():
    reply = "Essaie de marcher 10 minutes puis bois un verre d'eau."
    guarded = guard_unapproved_behavior(
        reply,
        language="fr",
        approved_session_context=False,
    )
    assert "marcher" not in guarded.lower()
    assert "bois" not in guarded.lower()
    assert "rappel" in guarded.lower()


def test_guard_allows_organization_of_recorded_health_topics():
    reply = "Note tes glycémies, ton alimentation et ton humeur dans la même liste."
    assert guard_unapproved_behavior(
        reply,
        language="fr",
        approved_session_context=False,
    ) == reply


def test_guard_preserves_reply_with_approved_context():
    reply = "Essaie de marcher 10 minutes."
    assert guard_unapproved_behavior(
        reply,
        language="fr",
        approved_session_context=True,
    ) == reply


def test_guard_keeps_latin_darija_fallback_script():
    guarded = guard_unapproved_behavior(
        "Dir riayada 10 d9aye9.",
        language="ar-MA",
        approved_session_context=False,
        prefer_latin_script=True,
    )
    assert "reminder" in guarded.lower()
    assert not any("\u0600" <= char <= "\u06ff" for char in guarded)
