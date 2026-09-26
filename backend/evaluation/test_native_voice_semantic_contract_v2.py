from evaluation.native_voice_batched_benchmark import APPROVED_SEMANTICS, SYSTEM_PROMPT


def test_clinician_prep_is_closed_to_two_question_intents():
    contract = APPROVED_SEMANTICS["clinician_prep"]

    assert contract["allowed_question_intents"] == [
        "Ask the clinician how to discuss the irregular logging times observed this week.",
        "Ask whether this observation alone is sufficient for any clinical conclusion.",
    ]


def test_clinician_prep_forbids_cause_glucose_lifestyle_medication_treatment_and_dose():
    forbidden = set(APPROVED_SEMANTICS["clinician_prep"]["forbidden_claims"])

    assert {
        "Cause of the irregular logging",
        "Effect on blood glucose",
        "Lifestyle recommendation",
        "Medication recommendation",
        "Treatment recommendation",
        "Dose change",
        "New clinical interpretation",
    } <= forbidden


def test_non_english_locale_must_not_copy_english_contract_text():
    assert "NEVER copy English contract text into a non-English locale" in SYSTEM_PROMPT
