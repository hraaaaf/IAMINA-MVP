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
