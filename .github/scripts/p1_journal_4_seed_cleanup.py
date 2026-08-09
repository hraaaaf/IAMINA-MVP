from pathlib import Path

nutrition = Path('frontend/lib/core/data/nutrition_catalog.dart')
text = nutrition.read_text()
needle = "  MealNutritionProfile(foodId: 'tajine'),\n];"
insert = """  MealNutritionProfile(foodId: 'tajine'),
  MealNutritionProfile(
    foodId: 'apple',
    carbohydrate: NutritionReferenceValue(
      carbsPer100gLow: 14.2,
      carbsPer100gHigh: 15.7,
      sourceId: 'usda_fdc_2026',
      sourceFoodRef: 'FDC 1105664, 1105547, 1105781, 1105430, 1105897',
      evidenceTier: NutritionEvidenceTier.analytical,
    ),
  ),
  MealNutritionProfile(
    foodId: 'banana',
    carbohydrate: NutritionReferenceValue(
      carbsPer100gLow: 20.1,
      carbsPer100gHigh: 23.0,
      sourceId: 'usda_fdc_2026',
      sourceFoodRef: 'FDC 790774 and 790991',
      evidenceTier: NutritionEvidenceTier.analytical,
    ),
    portions: [
      NutritionPortion(
        id: 'one_peeled',
        label: LocalizedPortionLabel(
          fr: '1 banane pelée',
          en: '1 peeled banana',
          ar: 'موزة مقشرة واحدة',
        ),
        gramsLow: 110,
        gramsHigh: 115,
      ),
    ],
  ),
];"""
if "foodId: 'apple'" not in text:
    if needle not in text:
        raise SystemExit('nutrition insertion anchor missing')
    text = text.replace(needle, insert)
    nutrition.write_text(text)

test = Path('frontend/test/core/data/nutrition_catalog_test.dart')
t = test.read_text()
anchor = "    test('portion selections encode and decode without derived nutrients', () {"
new_test = """    test('USDA seed retains analytical ranges instead of false precision', () {
      final apple = nutritionProfileFor('apple')!;
      final banana = nutritionProfileFor('banana')!;

      expect(apple.carbohydrate!.carbsPer100gLow, 14.2);
      expect(apple.carbohydrate!.carbsPer100gHigh, 15.7);
      expect(apple.carbohydrate!.sourceFoodRef, contains('1105664'));
      expect(apple.carbohydrate!.sourceFoodRef, contains('1105897'));

      expect(banana.carbohydrate!.carbsPer100gLow, 20.1);
      expect(banana.carbohydrate!.carbsPer100gHigh, 23.0);
      expect(banana.carbohydrate!.sourceFoodRef, contains('790774'));
      expect(banana.carbohydrate!.sourceFoodRef, contains('790991'));
      final oneBanana = banana.portions.single;
      expect(oneBanana.id, 'one_peeled');
      expect(oneBanana.gramsLow, 110);
      expect(oneBanana.gramsHigh, 115);

      final estimate = estimateCarbsForPortion('banana', oneBanana)!;
      expect(estimate.isExact, isFalse);
      expect(estimate.low, closeTo(22.11, 0.01));
      expect(estimate.high, closeTo(26.45, 0.01));
    });

"""
if 'USDA seed retains analytical ranges' not in t:
    if anchor not in t:
        raise SystemExit('test insertion anchor missing')
    t = t.replace(anchor, new_test + anchor)
    test.write_text(t)
