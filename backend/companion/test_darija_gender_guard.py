from companion.output_guard import guard_narrator_output


def test_guard_rejects_darija_masculine_feminine_mismatch():
    reply = "خليها بسيطة: ثلاث خانات خاويين بلا محتوى مفروض، وعمر غير باللي نتا اخترتي من قبل."
    guarded = guard_narrator_output(
        reply,
        language="ar-MA",
        approved_session_context=False,
        mode="practical",
    )
    assert "نتا اخترتي" not in guarded
