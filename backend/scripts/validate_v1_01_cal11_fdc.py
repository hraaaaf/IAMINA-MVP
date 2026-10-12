"""Offline CAL-11 source oracle for USDA Foundation Foods April 2026.

The official download (NOT included in this repository) is available at:
https://fdc.nal.usda.gov/download-datasets/

Example:
    python scripts/validate_v1_01_cal11_fdc.py /path/to/USDA_foundation_2026.zip

Fail closed if a published FDC ID, food description, carbohydrate nutrient or
catalogue numeric range does not match the *primary* archive. This script
does not verify banana edible weight 110–115 g; that needs separate USDA
portion-level provenance and human curation. No medical treatment inference.
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
from zipfile import BadZipFile, ZipFile

SEED = {
    "apple": {
        "ids": (1105664, 1105547, 1105781, 1105430, 1105897),
        "min": 14.2,
        "max": 15.7,
    },
    "banana": {
        "ids": (790774, 790991),
        "min": 20.1,
        "max": 23.0,
    },
}
CARBOHYDRATE_NUTRIENT_ID = 1005
RELEASE = "2026-04"


def _foundation_rows(zip_file: ZipFile) -> list[dict]:
    """Read only the official FoundationFoods JSON payload from the ZIP."""
    candidates = [
        name
        for name in zip_file.namelist()
        if name.lower().endswith(".json") and not name.startswith("__MACOSX/")
    ]
    for name in candidates:
        payload = json.loads(zip_file.read(name))
        if not isinstance(payload, dict):
            continue
        rows = payload.get("FoundationFoods")
        if isinstance(rows, list):
            # The official 2026-04 USDA JSON contains null placeholders in
            # FoundationFoods. Ignore only JSON null: never ignore unknown
            # types or silently transform malformed nutritional source rows.
            if any(item is not None and not isinstance(item, dict) for item in rows):
                raise ValueError("FoundationFoods must contain objects or null only")
            non_null_rows = [item for item in rows if item is not None]
            if not non_null_rows:
                raise ValueError("FoundationFoods has no source objects")
            return non_null_rows
    raise ValueError("FoundationFoods list missing from primary USDA JSON archive")


def _carbohydrate_amount(food: dict) -> float:
    nutrient_rows = food.get("foodNutrients")
    if not isinstance(nutrient_rows, list):
        raise ValueError("foodNutrients array absent")
    matches = []
    for item in nutrient_rows:
        if not isinstance(item, dict):
            continue
        nutrient = item.get("nutrient")
        if not isinstance(nutrient, dict):
            continue
        if nutrient.get("id") == CARBOHYDRATE_NUTRIENT_ID:
            if nutrient.get("unitName") != "G":
                raise ValueError("carbohydrate unit is not grams per 100g")
            value = item.get("amount")
            if not isinstance(value, (float, int)) or isinstance(value, bool):
                raise ValueError("carbohydrate amount not numeric")
            if not isfinite(value) or value < 0:
                raise ValueError("carbohydrate amount invalid")
            matches.append(float(value))
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one carbohydrate nutrient 1005; got {len(matches)}"
        )
    return matches[0]


def validate_zip(path: Path) -> dict[str, list[dict]]:
    """Verify each pinned FDC ID, food family, and carbohydrate range."""
    if not path.is_file():
        raise ValueError("USDA archive file missing")
    try:
        with ZipFile(path) as archive:
            rows = _foundation_rows(archive)
    except (BadZipFile, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("invalid USDA ZIP/JSON archive") from exc
    seen: dict[int, dict] = {}
    for row in rows:
        fdc_id = row.get("fdcId")
        if type(fdc_id) is int:
            if fdc_id in seen:
                raise ValueError(f"duplicate source FDC ID {fdc_id}")
            seen[fdc_id] = row
    # Fail closed across the entire catalog, not just the first absent ID:
    # report every missing official 2026 Foundation record to support a
    # qualified source-by-source curation decision.
    missing_by_family = {
        family: [fdc_id for fdc_id in rule["ids"] if fdc_id not in seen]
        for family, rule in SEED.items()
    }
    if any(missing_by_family.values()):
        gaps = "; ".join(
            f"{family}: {', '.join(map(str, missing_ids))}"
            for family, missing_ids in missing_by_family.items()
            if missing_ids
        )
        raise ValueError(
            "missing official Foundation FDC IDs (no automatic source "
            f"substitution): {gaps}"
        )

    output: dict[str, list[dict]] = {}
    for food_name, rule in SEED.items():
        evidence: list[dict] = []
        for fdc_id in rule["ids"]:
            food = seen.get(fdc_id)
            if food is None:
                raise ValueError(f"{food_name}: FDC {fdc_id} missing")
            description = food.get("description")
            if not isinstance(description, str) or food_name not in description.lower():
                raise ValueError(f"FDC {fdc_id} does not describe {food_name}")
            amount = _carbohydrate_amount(food)
            if not rule["min"] <= amount <= rule["max"]:
                raise ValueError(
                    f"{food_name} FDC {fdc_id}: carbohydrate {amount} outside "
                    f"pinned [{rule['min']}, {rule['max']}]"
                )
            evidence.append(
                {"fdcId": fdc_id, "description": description, "carb_g_per_100g": amount}
            )
        output[food_name] = evidence
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Original USDA 2026-04 Foundation JSON zip")
    args = parser.parse_args()
    try:
        evidence = validate_zip(args.archive)
    except ValueError as exc:
        parser.exit(2, f"CAL-11 BLOCKED/FAIL: {exc}\n")
    print(
        json.dumps(
            {"status": "SOURCE_ROWS_MATCH", "release": RELEASE, "evidence": evidence},
            indent=2,
        )
    )
    print("NOTE: banana portion gram weights and clinical suitability NOT certified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
