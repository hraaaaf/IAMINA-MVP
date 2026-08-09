import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:amina/core/data/nutrition_catalog.dart';

void main() {
  group('Nutrition Data v2 truthfulness contract', () {
    test('all declared sources carry publisher and version provenance', () {
      expect(nutritionSources, isNotEmpty);
      for (final source in nutritionSources.values) {
        expect(source.id.trim(), isNotEmpty);
        expect(source.title.trim(), isNotEmpty);
        expect(source.publisher.trim(), isNotEmpty);
        expect(source.version.trim(), isNotEmpty);
        expect(source.year, greaterThan(1900));
      }
    });

    test('Morocco-first natural portions are available without fake weights', () {
      final msemen = nutritionProfileFor('msemen');
      final bread = nutritionProfileFor('moroccan_bread');
      final couscous = nutritionProfileFor('couscous');
      final harira = nutritionProfileFor('harira');

      expect(msemen, isNotNull);
      expect(bread, isNotNull);
      expect(couscous, isNotNull);
      expect(harira, isNotNull);

      expect(msemen!.portions.map((p) => p.id), contains('one_piece'));
      expect(bread!.portions.map((p) => p.id), contains('quarter'));
      expect(couscous!.portions.map((p) => p.id), contains('medium_plate'));
      expect(harira!.portions.map((p) => p.id), contains('medium_bowl'));

      for (final profile in [msemen, bread, couscous, harira]) {
        for (final portion in profile.portions) {
          expect(portion.grams, isNull);
          expect(portion.gramsLow, isNull);
          expect(portion.gramsHigh, isNull);
        }
      }
    });

    test('unsupported Moroccan portions fail closed instead of inventing carbs', () {
      final msemen = nutritionProfileFor('msemen')!;
      expect(msemen.hasDocumentedCarbohydrate, isFalse);
      expect(estimateCarbsForGrams('msemen', 100), isNull);
      expect(estimateCarbsForPortion('msemen', msemen.portions.first), isNull);
    });

    test('invalid gram quantities never produce an estimate', () {
      expect(estimateCarbsForGrams('msemen', 0), isNull);
      expect(estimateCarbsForGrams('msemen', -1), isNull);
      expect(estimateCarbsForGrams('msemen', double.nan), isNull);
    });

    test('portion vocabulary remains trilingual', () {
      final portion = nutritionProfileFor('moroccan_bread')!.portions.first;
      expect(portion.label.forLocale(const Locale('fr')), '¼ pain');
      expect(portion.label.forLocale(const Locale('en')), '¼ loaf');
      expect(portion.label.forLocale(const Locale('ar')), '¼ خبزة');
    });

    test('source registry includes Morocco, ANSES and USDA foundations', () {
      expect(nutritionSourceFor('morocco_fct_2020'), isNotNull);
      expect(nutritionSourceFor('ciqual_2025'), isNotNull);
      expect(nutritionSourceFor('usda_fdc_2026'), isNotNull);
    });

    test('portion selections encode and decode without derived nutrients', () {
      const selection = MealPortionSelection(
        foodId: 'msemen',
        portionId: 'one_piece',
      );
      final raw = encodeMealPortionSelections(const [selection]);
      expect(raw, contains('food_id'));
      expect(raw, contains('portion_id'));
      expect(raw, isNot(contains('carbs')));
      expect(raw, isNot(contains('calories')));
      expect(raw, isNot(contains('glycemic_index')));

      final decoded = decodeMealPortionSelections(raw);
      expect(decoded, hasLength(1));
      expect(decoded.single.foodId, 'msemen');
      expect(decoded.single.portionId, 'one_piece');
      expect(decoded.single.grams, isNull);
    });
  });
}
