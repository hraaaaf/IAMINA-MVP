from companion.diabetes_education import diabetes_education_reply


def test_common_cgm_concepts_have_useful_deterministic_copy():
    cases = (
        ("Explique-moi le TIR", "fr", "70–180"),
        ("What is glucose variability?", "en", "36%"),
        ("What is GMI?", "en", "laboratory A1C"),
        ("Explique le temps au-dessus de la cible", "fr", ">180"),
        ("C'est quoi la glycémie moyenne ?", "fr", "TIR/TBR/TAR"),
    )
    for message, language, expected in cases:
        reply = diabetes_education_reply(message, language)
        assert reply is not None
        assert expected in reply


def test_tir_copy_supports_arabic_and_darija_scripts():
    msa = diabetes_education_reply("ما هو TIR؟", "ar")
    darija_ar = diabetes_education_reply("شنو هو TIR؟", "ar-MA")
    darija_latin = diabetes_education_reply("chno howa TIR?", "ar-MA")

    assert msa and "70" in msa
    assert darija_ar and "70" in darija_ar
    assert darija_latin and "70" in darija_latin
    assert not any("\u0600" <= ch <= "\u06ff" for ch in darija_latin)


def test_unknown_question_does_not_hijack_free_form_conversation():
    assert diabetes_education_reply("Parle-moi de ma journée", "fr") is None
