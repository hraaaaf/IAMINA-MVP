import pytest

from evaluation.dialect_dataset_groq_benchmark import (
    CASES_PER_COUNTRY,
    EXPECTED_LICENSE,
    TARGETS,
    BenchmarkConfigurationError,
    SourceSnapshot,
    _parse_country_code,
    _privacy_screen,
    _validate_source_url,
    build_cases,
)


def _row(row_id, country, text):
    return {
        "id": str(row_id),
        "source_country": country,
        "source_text": text,
    }


def test_target_coverage_is_exact_mena_set():
    assert sorted(TARGETS) == ["AE", "KW", "MA", "OM", "QA", "SA"]
    assert CASES_PER_COUNTRY == 3


def test_privacy_screen_rejects_obvious_pii_and_noise():
    assert _privacy_screen("تكفين خليني أروح، قولي له يخليني أروح") is True
    assert _privacy_screen("ليش ما نزلت") is True
    assert _privacy_screen("[03/06, 2:06 am] Ahmed: الله يحفظ الجميع") is False
    assert _privacy_screen("+973 3849 9318 الله يحفظ الجميع") is False
    assert _privacy_screen("راسلني على user@example.com لو سمحت") is False
    assert _privacy_screen("https://example.com هذا رابط طويل") is False
    assert _privacy_screen("short") is False


def test_source_urls_are_https_and_huggingface_only():
    _validate_source_url("https://huggingface.co/api/datasets/example/repo")
    with pytest.raises(BenchmarkConfigurationError):
        _validate_source_url("http://huggingface.co/api/datasets/example/repo")
    with pytest.raises(BenchmarkConfigurationError):
        _validate_source_url("file:///tmp/dataset.csv")
    with pytest.raises(BenchmarkConfigurationError):
        _validate_source_url("https://example.com/dataset.csv")


def test_plain_country_code_contract_is_strict():
    assert _parse_country_code("sa") == "SA"
    assert _parse_country_code(" QA\n") == "QA"
    with pytest.raises(BenchmarkConfigurationError):
        _parse_country_code("SA because this sounds Saudi")
    with pytest.raises(BenchmarkConfigurationError):
        _parse_country_code('{"country_code":"SA"}')


def test_build_cases_is_deterministic_and_does_not_need_raw_text_in_report():
    gulf_rows = []
    labels = {
        "SA": "saudi arabia",
        "AE": "united arab emirates",
        "KW": "kuwait",
        "QA": "qatar",
        "OM": "oman",
    }
    counter = 1
    for label in labels.values():
        for text in (
            "هذي جملة محلية واضحة للاختبار بدون أي معلومات شخصية",
            "هذا مثال ثاني طويل بما يكفي ويستخدم كلام يومي بسيط",
            "وهذا مثال ثالث للمقارنة بين اللهجات بطريقة محايدة وآمنة",
        ):
            gulf_rows.append(_row(counter, label, text))
            counter += 1
    ma_rows = [
        _row(1, "morocco", "هاد مثال مغربي واضح وطويل بلا حتى معلومة شخصية"),
        _row(2, "morocco", "هاد جملة ثانية بالدارجة باش نجربو الفهم ديال اللهجة"),
        _row(3, "morocco", "وهذا مثال ثالث مغربي بسيط ومحايد من غير بيانات شخصية"),
    ]
    snapshots = {
        "ebubekr53/organic-gulf-arabic-dialect-dataset": SourceSnapshot(
            repo_id="ebubekr53/organic-gulf-arabic-dialect-dataset",
            revision="a" * 40,
            license=EXPECTED_LICENSE,
            csv_path="data.csv",
            rows=tuple(gulf_rows),
        ),
        "ebubekr53/organic-maghrebi-arabic-dialect-dataset": SourceSnapshot(
            repo_id="ebubekr53/organic-maghrebi-arabic-dialect-dataset",
            revision="b" * 40,
            license=EXPECTED_LICENSE,
            csv_path="data.csv",
            rows=tuple(ma_rows),
        ),
    }
    cases = build_cases(snapshots)
    assert len(cases) == 18
    assert [case.country_code for case in cases].count("MA") == 3
    assert cases[0].case_id == "sa-1"
    assert all(_privacy_screen(case.text) for case in cases)
