import 'package:flutter/widgets.dart';

/// Evidence tier for one patient-facing nutrition value.
///
/// A value may be shown only when it has a source and an explicit evidence
/// tier. Missing or weakly mapped values fail closed instead of being guessed.
enum NutritionEvidenceTier {
  analytical,
  compiled,
  label,
}

class NutritionSourceRef {
  final String id;
  final String title;
  final String publisher;
  final String version;
  final int year;

  const NutritionSourceRef({
    required this.id,
    required this.title,
    required this.publisher,
    required this.version,
    required this.year,
  });
}

class LocalizedPortionLabel {
  final String fr;
  final String en;
  final String ar;

  const LocalizedPortionLabel({
    required this.fr,
    required this.en,
    required this.ar,
  });

  String forLocale(Locale locale) {
    if (locale.languageCode == 'ar') return ar;
    if (locale.languageCode == 'en') return en;
    return fr;
  }
}

class NutritionPortion {
  final String id;
  final LocalizedPortionLabel label;

  /// Exact source-backed edible weight when available.
  final double? grams;

  /// Source-backed plausible interval when an exact household portion is not
  /// defensible. Both bounds must be present together.
  final double? gramsLow;
  final double? gramsHigh;

  const NutritionPortion({
    required this.id,
    required this.label,
    this.grams,
    this.gramsLow,
    this.gramsHigh,
  }) : assert(
         grams == null || (gramsLow == null && gramsHigh == null),
         'Use either an exact weight or a range, never both.',
       ),
       assert(
         (gramsLow == null) == (gramsHigh == null),
         'Portion ranges require both bounds.',
       );
}

class NutritionReferenceValue {
  /// Carbohydrate reference expressed per 100 g edible portion.
  ///
  /// Exact values use the same low/high value. Ranges retain documented
  /// uncertainty instead of presenting false precision.
  final double carbsPer100gLow;
  final double carbsPer100gHigh;
  final String sourceId;
  final String sourceFoodRef;
  final NutritionEvidenceTier evidenceTier;

  const NutritionReferenceValue({
    required this.carbsPer100gLow,
    required this.carbsPer100gHigh,
    required this.sourceId,
    required this.sourceFoodRef,
    required this.evidenceTier,
  }) : assert(carbsPer100gLow >= 0),
       assert(carbsPer100gHigh >= carbsPer100gLow);
}

class MealNutritionProfile {
  final String foodId;
  final NutritionReferenceValue? carbohydrate;
  final List<NutritionPortion> portions;

  const MealNutritionProfile({
    required this.foodId,
    this.carbohydrate,
    this.portions = const <NutritionPortion>[],
  });

  bool get hasDocumentedCarbohydrate => carbohydrate != null;
}

class CarbEstimate {
  final double low;
  final double high;
  final String sourceId;
  final String sourceFoodRef;

  const CarbEstimate({
    required this.low,
    required this.high,
    required this.sourceId,
    required this.sourceFoodRef,
  });

  bool get isExact => (high - low).abs() < 0.01;
}

const Map<String, NutritionSourceRef> nutritionSources = {
  'morocco_fct_2020': NutritionSourceRef(
    id: 'morocco_fct_2020',
    title: 'Moroccan food composition tables',
    publisher: 'Khalis et al. / Journal of Food Composition and Analysis',
    version: '2020',
    year: 2020,
  ),
  'ciqual_2025': NutritionSourceRef(
    id: 'ciqual_2025',
    title: 'Table Ciqual',
    publisher: 'ANSES',
    version: '2025',
    year: 2025,
  ),
  'usda_fdc_2026': NutritionSourceRef(
    id: 'usda_fdc_2026',
    title: 'FoodData Central',
    publisher: 'USDA Agricultural Research Service',
    version: '2026-04',
    year: 2026,
  ),
};

/// Morocco-first portion vocabulary. Numeric weights are intentionally absent
/// until the exact supplementary/source row has been curated and reviewed.
/// The user can still record the natural portion without IAMINA inventing a
/// carbohydrate value.
const List<MealNutritionProfile> mealNutritionProfiles = [
  MealNutritionProfile(
    foodId: 'moroccan_bread',
    portions: [
      NutritionPortion(
        id: 'quarter',
        label: LocalizedPortionLabel(
          fr: '¼ pain',
          en: '¼ loaf',
          ar: '¼ خبزة',
        ),
      ),
      NutritionPortion(
        id: 'half',
        label: LocalizedPortionLabel(
          fr: '½ pain',
          en: '½ loaf',
          ar: '½ خبزة',
        ),
      ),
      NutritionPortion(
        id: 'whole',
        label: LocalizedPortionLabel(
          fr: '1 pain',
          en: '1 loaf',
          ar: 'خبزة واحدة',
        ),
      ),
    ],
  ),
  MealNutritionProfile(
    foodId: 'msemen',
    portions: [
      NutritionPortion(
        id: 'half_piece',
        label: LocalizedPortionLabel(
          fr: '½ msemen',
          en: '½ msemen',
          ar: '½ مسمن',
        ),
      ),
      NutritionPortion(
        id: 'one_piece',
        label: LocalizedPortionLabel(
          fr: '1 msemen',
          en: '1 msemen',
          ar: 'مسمن واحد',
        ),
      ),
      NutritionPortion(
        id: 'two_pieces',
        label: LocalizedPortionLabel(
          fr: '2 msemen',
          en: '2 msemen',
          ar: '2 مسمن',
        ),
      ),
    ],
  ),
  MealNutritionProfile(
    foodId: 'couscous',
    portions: [
      NutritionPortion(
        id: 'small_plate',
        label: LocalizedPortionLabel(
          fr: 'Petite assiette',
          en: 'Small plate',
          ar: 'طبق صغير',
        ),
      ),
      NutritionPortion(
        id: 'medium_plate',
        label: LocalizedPortionLabel(
          fr: 'Assiette moyenne',
          en: 'Medium plate',
          ar: 'طبق متوسط',
        ),
      ),
      NutritionPortion(
        id: 'large_plate',
        label: LocalizedPortionLabel(
          fr: 'Grande assiette',
          en: 'Large plate',
          ar: 'طبق كبير',
        ),
      ),
    ],
  ),
  MealNutritionProfile(
    foodId: 'harira',
    portions: [
      NutritionPortion(
        id: 'small_bowl',
        label: LocalizedPortionLabel(
          fr: 'Petit bol',
          en: 'Small bowl',
          ar: 'زلافة صغيرة',
        ),
      ),
      NutritionPortion(
        id: 'medium_bowl',
        label: LocalizedPortionLabel(
          fr: 'Bol moyen',
          en: 'Medium bowl',
          ar: 'زلافة متوسطة',
        ),
      ),
    ],
  ),
  MealNutritionProfile(foodId: 'tajine'),
];

final Map<String, MealNutritionProfile> _nutritionByFoodId = {
  for (final profile in mealNutritionProfiles) profile.foodId: profile,
};

MealNutritionProfile? nutritionProfileFor(String foodId) =>
    _nutritionByFoodId[foodId];

NutritionSourceRef? nutritionSourceFor(String sourceId) =>
    nutritionSources[sourceId];

CarbEstimate? estimateCarbsForGrams(String foodId, double grams) {
  if (!grams.isFinite || grams <= 0) return null;
  final profile = nutritionProfileFor(foodId);
  final ref = profile?.carbohydrate;
  if (ref == null) return null;
  return CarbEstimate(
    low: ref.carbsPer100gLow * grams / 100,
    high: ref.carbsPer100gHigh * grams / 100,
    sourceId: ref.sourceId,
    sourceFoodRef: ref.sourceFoodRef,
  );
}

CarbEstimate? estimateCarbsForPortion(
  String foodId,
  NutritionPortion portion,
) {
  final profile = nutritionProfileFor(foodId);
  final ref = profile?.carbohydrate;
  if (ref == null) return null;
  if (portion.grams != null) {
    return estimateCarbsForGrams(foodId, portion.grams!);
  }
  if (portion.gramsLow == null || portion.gramsHigh == null) return null;
  return CarbEstimate(
    low: ref.carbsPer100gLow * portion.gramsLow! / 100,
    high: ref.carbsPer100gHigh * portion.gramsHigh! / 100,
    sourceId: ref.sourceId,
    sourceFoodRef: ref.sourceFoodRef,
  );
}
