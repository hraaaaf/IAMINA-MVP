from evaluation.p5_2_arabic_camera_bounded_benchmark import (
    ARABIC_CASES,
    NUMERIC_CASES,
    normalize_text,
    numeric_tokens,
    select_annotations,
)


def test_digit_normalization_is_exact_across_arabic_persian_ascii():
    assert numeric_tokens("١٢٫٥ 34 ۶۷") == ("12.5", "34", "67")


def test_text_normalization_removes_diacritics_spacing_not_letters():
    assert normalize_text("السِّعر: ١٢") == normalize_text("السعر 12")


def test_selection_is_deterministic_and_never_result_tuned():
    rows = []
    for row_id in range(1, 8):
        rows.append({
            "id": row_id,
            "annotations": [
                {"text": f"مرحبا{chr(0x627 + (row_id % 5))}", "box": [0, 0, 20, 0, 20, 10, 0, 10]},
                {"text": str(100 + row_id), "box": [0, 10, 20, 10, 20, 20, 0, 20]},
            ],
        })
    selected = select_annotations(reversed(rows))
    assert len(selected) == ARABIC_CASES + NUMERIC_CASES
    assert [case.row_id for case in selected[:ARABIC_CASES]] == list(range(1, ARABIC_CASES + 1))
    assert [case.row_id for case in selected[ARABIC_CASES:]] == list(range(1, NUMERIC_CASES + 1))
    assert all(case.kind == "arabic_text" for case in selected[:ARABIC_CASES])
    assert all(case.kind == "numeric" for case in selected[ARABIC_CASES:])
