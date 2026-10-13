"""Synthetic tests for the CAL-11 USDA primary-archive oracle.

These fixture rows are invented, deliberately NOT primary USDA nutrition
evidence. Only executing the validator on the downloaded USDA April 2026
Foundation archive can verify the repository's published FDC IDs and ranges.
"""

import json
from zipfile import ZipFile

import pytest

from scripts.validate_v1_01_cal11_fdc import SEED, validate_zip


def _synthetic_archive(tmp_path, *, modify=None):
    rows = []
    for family, rule in SEED.items():
        for fdc_id in rule["ids"]:
            rows.append(
                {
                    "fdcId": fdc_id,
                    "description": f"synthetic {family} test food",
                    "foodPortions": (
                        [
                            {
                                "measureUnit": {"name": "Banana"},
                                "modifier": "Peeled",
                                "gramWeight": rule["peeled_grams"][fdc_id],
                            }
                        ]
                        if family == "banana"
                        else []
                    ),
                    "foodNutrients": [
                        {
                            "nutrient": {
                                "id": 1005,
                                "name": "Carbohydrate, by difference",
                                "unitName": "G",
                            },
                            "amount": rule["min"],
                        }
                    ],
                }
            )
    if modify is not None:
        modify(rows)
    path = tmp_path / "SYNTHETIC_NOT_USDA.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("foundation_food.json", json.dumps({"FoundationFoods": rows}))
    return path


def test_synthetic_fixture_accepts_all_required_ids_without_certifying_usda(tmp_path):
    result = validate_zip(_synthetic_archive(tmp_path))
    assert tuple(result) == ("apple", "banana")
    assert len(result["apple"]) == 5
    assert len(result["banana"]) == 2
    assert all(row["carb_g_per_100g"] > 0 for value in result.values() for row in value)


def test_official_json_null_placeholders_do_not_hide_source_rows(tmp_path):
    # USDA April 2026 contains null placeholders in the official FoundationFoods
    # array. Preserve all source objects and only ignore null array entries.
    result = validate_zip(
        _synthetic_archive(
            tmp_path,
            modify=lambda rows: rows.insert(0, None),
        )
    )
    assert len(result["apple"]) == 5
    assert len(result["banana"]) == 2


def test_source_oracle_rejects_non_null_malformed_rows(tmp_path):
    with pytest.raises(ValueError, match="objects or null only"):
        validate_zip(
            _synthetic_archive(
                tmp_path,
                modify=lambda rows: rows.insert(0, "SYNTHETIC_MALFORMED_ROW"),
            )
        )


def test_multiple_missing_usda_ids_are_reported_before_numeric_proofs(tmp_path):
    # Both categories can diverge from the frozen USDA Foundation release.
    # The audit must report the whole failure surface, never the first only.
    def remove_two_foods(rows):
        rows[:] = [
            food
            for food in rows
            if food["fdcId"] not in (1750339, 1105314)
        ]

    with pytest.raises(ValueError) as caught:
        validate_zip(_synthetic_archive(tmp_path, modify=remove_two_foods))
    assert "missing official Foundation FDC IDs" in str(caught.value)
    assert "apple: 1750339" in str(caught.value)
    assert "banana: 1105314" in str(caught.value)
    assert "no automatic source substitution" in str(caught.value)



def test_official_peeled_banana_portion_weights_are_checked(tmp_path):
    result = validate_zip(_synthetic_archive(tmp_path))
    banana = result["banana"]
    assert {row["fdcId"]: row["peeled_grams"] for row in banana} == {
        1105073: 110.0,
        1105314: 115.0,
    }


@pytest.mark.parametrize("bad_weight", [None, 0, -1, 123.0, float("nan")])
def test_wrong_peeled_banana_weight_fails_closed(tmp_path, bad_weight):
    def corrupt_portion(rows):
        banana = next(row for row in rows if row["fdcId"] == 1105073)
        banana["foodPortions"][0]["gramWeight"] = bad_weight

    with pytest.raises(ValueError, match="gramWeight"):
        validate_zip(_synthetic_archive(tmp_path, modify=corrupt_portion))


def test_missing_peeled_banana_portion_fails_closed(tmp_path):
    def remove_portion(rows):
        banana = next(row for row in rows if row["fdcId"] == 1105073)
        banana["foodPortions"].clear()

    with pytest.raises(ValueError, match="expected one banana peeled"):
        validate_zip(_synthetic_archive(tmp_path, modify=remove_portion))


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda rows: rows.pop(), "missing"),
        (lambda rows: rows[0].update(description="synthetic banana"), "does not describe"),
        (
            lambda rows: rows[0]["foodNutrients"][0].update(amount=999),
            "outside pinned",
        ),
        (
            lambda rows: rows[0]["foodNutrients"].clear(),
            "exactly one",
        ),
        (
            lambda rows: rows[0]["foodNutrients"][0]["nutrient"].update(unitName="MG"),
            "not grams",
        ),
        (
            lambda rows: rows.append(rows[0].copy()),
            "duplicate source",
        ),
    ],
)
def test_source_oracle_fails_closed_for_missing_invalid_or_ambiguous_rows(
    tmp_path, change, expected
):
    with pytest.raises(ValueError, match=expected):
        validate_zip(_synthetic_archive(tmp_path, modify=change))


def test_source_oracle_rejects_missing_or_unparseable_archive(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        validate_zip(tmp_path / "not-present.zip")
    invalid = tmp_path / "not-a-real-usda.zip"
    invalid.write_text("synthetic invalid ZIP", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid USDA"):
        validate_zip(invalid)
