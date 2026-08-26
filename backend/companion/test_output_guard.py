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


def test_guard_allows_abstract_organization_copy():
    reply = "Mets un rappel et garde une checklist courte."
    assert guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
    ) == reply


def test_guard_does_not_treat_context_presence_as_behavior_authorization():
    reply = "Essaie de marcher 10 minutes."
    guarded = guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=True,
    )
    assert guarded != reply
    assert "rappel" in guarded.lower()


def test_guard_replaces_overlong_week_plan_with_empty_structure():
    reply = " ".join(["organisation"] * 46)
    guarded = guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
        mode="practical",
        weekly=True,
    )
    assert "trois cases vides" in guarded
    assert "médecin" not in guarded.lower()


def test_guard_uses_stronger_compression_for_very_long_output():
    medium = guard_narrator_output(
        " ".join(["organisation"] * 50),
        language="fr",
        approved_session_context=False,
    )
    very_long = guard_narrator_output(
        " ".join(["organisation"] * 70),
        language="fr",
        approved_session_context=False,
    )
    assert medium != very_long
    assert "un seul repère" in medium
    assert "Réduis au minimum" in very_long


def test_guard_blocks_model_selected_tracking_content():
    guarded = guard_narrator_output(
        "Note 1 point sur ton humeur chaque lundi.",
        language="fr",
        approved_session_context=False,
    )
    assert "humeur" not in guarded.lower()
    assert "rappel" in guarded.lower()


def test_guard_blocks_arabizi_content_selection():
    guarded = guard_narrator_output(
        "Sji mood dyalk f checklist.",
        language="ar-MA",
        approved_session_context=False,
        prefer_latin_script=True,
    )
    assert "mood" not in guarded.lower()
    assert "reminder" in guarded.lower()


def test_guard_bounds_emotional_shape():
    reply = "\n".join(("Première phrase empathique.", "Deuxième ligne avec un plan."))
    guarded = guard_narrator_output(
        reply,
        language="fr",
        approved_session_context=False,
        mode="emotional",
    )
    assert "plan" not in guarded.lower()
    assert "moment" in guarded.lower()


def test_guard_keeps_latin_darija_fallback_script():
    guarded = guard_narrator_output(
        "Dir riayada 10 d9aye9.",
        language="ar-MA",
        approved_session_context=False,
        prefer_latin_script=True,
    )
    assert "reminder" in guarded.lower()
    assert not any("\u0600" <= char <= "\u06ff" for char in guarded)
