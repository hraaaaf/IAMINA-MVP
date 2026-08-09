import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"Expected exactly one match in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1))


add_log = ROOT / "frontend/lib/features/dashboard/widgets/add_log_sheet.dart"
replace_once(
    add_log,
    "import '../../../core/data/meal_food_catalog.dart';\n",
    "import '../../../core/data/meal_food_catalog.dart';\n"
    "import '../../../core/data/nutrition_catalog.dart';\n",
)
replace_once(
    add_log,
    "import '../../journal/widgets/meal_capture_panel.dart';\n",
    "import '../../journal/widgets/meal_capture_panel.dart';\n"
    "import '../../journal/widgets/nutrition_portion_editor.dart';\n",
)
replace_once(
    add_log,
    "  final List<String> _selectedMealItemIds = <String>[];\n",
    "  final List<String> _selectedMealItemIds = <String>[];\n"
    "  final Map<String, MealPortionSelection> _mealPortionSelections =\n"
    "      <String, MealPortionSelection>{};\n",
)
replace_once(
    add_log,
    "                  _selectedMealItemIds.clear();\n                  _mealNoteController.clear();\n",
    "                  _selectedMealItemIds.clear();\n"
    "                  _mealPortionSelections.clear();\n"
    "                  _mealNoteController.clear();\n",
)
replace_once(
    add_log,
    "            onChanged: (ids) => setState(() {\n"
    "              _selectedMealItemIds\n"
    "                ..clear()\n"
    "                ..addAll(ids);\n"
    "            }),\n"
    "          ),\n"
    "          const SizedBox(height: 16),\n"
    "          TextField(\n",
    "            onChanged: (ids) => setState(() {\n"
    "              _selectedMealItemIds\n"
    "                ..clear()\n"
    "                ..addAll(ids);\n"
    "              _mealPortionSelections.removeWhere(\n"
    "                (foodId, _) => !ids.contains(foodId),\n"
    "              );\n"
    "            }),\n"
    "          ),\n"
    "          if (_selectedMealItemIds.isNotEmpty) ...<Widget>[\n"
    "            const SizedBox(height: 16),\n"
    "            NutritionPortionEditor(\n"
    "              selectedFoodIds: _selectedMealItemIds,\n"
    "              selections: _mealPortionSelections,\n"
    "              onChanged: (next) => setState(() {\n"
    "                _mealPortionSelections\n"
    "                  ..clear()\n"
    "                  ..addAll(next);\n"
    "              }),\n"
    "            ),\n"
    "          ],\n"
    "          const SizedBox(height: 16),\n"
    "          TextField(\n",
)
replace_once(
    add_log,
    "              mealItemsJson: drift.Value(\n"
    "                encodeMealItemIds(_selectedMealItemIds),\n"
    "              ),\n"
    "              clientUuid: const Uuid().v4(),\n",
    "              mealItemsJson: drift.Value(\n"
    "                encodeMealItemIds(_selectedMealItemIds),\n"
    "              ),\n"
    "              mealPortionsJson: drift.Value(\n"
    "                encodeMealPortionSelections(_mealPortionSelections.values),\n"
    "              ),\n"
    "              clientUuid: const Uuid().v4(),\n",
)

translations = {
    "fr": {
        "journalNutritionPortionTitle": "PORTIONS",
        "journalNutritionPortionHint": "Choisis une portion naturelle ou indique les grammes si tu les connais. Aucun chiffre nutritionnel n’est inventé.",
        "journalNutritionGrams": "Grammes",
        "journalNutritionUnavailable": "Nutrition non chiffrée : donnée ou portion pas encore assez documentée.",
        "journalNutritionCarbsExact": "≈ {value} g de glucides",
        "journalNutritionCarbsRange": "≈ {low}–{high} g de glucides",
        "journalNutritionSource": "Source : {source}",
    },
    "en": {
        "journalNutritionPortionTitle": "PORTIONS",
        "journalNutritionPortionHint": "Choose a natural portion or enter grams if you know them. No nutrition number is invented.",
        "journalNutritionGrams": "Grams",
        "journalNutritionUnavailable": "No numeric nutrition shown: the food or portion is not documented well enough yet.",
        "journalNutritionCarbsExact": "≈ {value} g carbohydrates",
        "journalNutritionCarbsRange": "≈ {low}–{high} g carbohydrates",
        "journalNutritionSource": "Source: {source}",
    },
    "ar": {
        "journalNutritionPortionTitle": "الكمية",
        "journalNutritionPortionHint": "اختر حصة مألوفة أو أدخل الوزن بالغرام إذا كنت تعرفه. لا يعرض IAmina رقماً غذائياً مخمناً.",
        "journalNutritionGrams": "غرام",
        "journalNutritionUnavailable": "لا توجد قيمة غذائية رقمية معروضة: الطعام أو الحصة غير موثقين بما يكفي بعد.",
        "journalNutritionCarbsExact": "≈ {value} غ كربوهيدرات",
        "journalNutritionCarbsRange": "≈ {low}–{high} غ كربوهيدرات",
        "journalNutritionSource": "المصدر: {source}",
    },
}

for locale, values in translations.items():
    path = ROOT / f"frontend/lib/l10n/app_{locale}.arb"
    data = json.loads(path.read_text())
    for key, value in values.items():
        data[key] = value
    for key in ("journalNutritionCarbsExact", "journalNutritionCarbsRange", "journalNutritionSource"):
        placeholders = {}
        if key == "journalNutritionCarbsExact":
            placeholders = {"value": {"type": "String"}}
        elif key == "journalNutritionCarbsRange":
            placeholders = {"low": {"type": "String"}, "high": {"type": "String"}}
        else:
            placeholders = {"source": {"type": "String"}}
        data[f"@{key}"] = {"placeholders": placeholders}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
