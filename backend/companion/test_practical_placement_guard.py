from companion.output_guard import guard_narrator_output


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
