import 'dart:convert';

import 'package:amina/core/data/meal_food_catalog.dart';

const _style = <String, Object>{
  'brand': 'IAMINA',
  'version': 'food-pictogram-v1',
  'master_size': 1024,
  'runtime_size': 256,
  'aspect_ratio': '1:1',
  'background': 'transparent',
  'camera': 'three-quarter top-down, consistent 38 degree angle',
  'lighting': 'soft premium studio light, gentle teal bounce, warm natural highlights',
  'material': 'realistic food illustration with refined editorial finish, not cartoon, not emoji',
  'composition': 'single food concept centered, 72 percent frame occupancy, subtle contact shadow',
  'accessibility': 'must remain identifiable at 48 px without relying on text or color alone',
  'forbidden': <String>[
    'text',
    'logo',
    'watermark',
    'hands',
    'people',
    'busy background',
    'decorative props that obscure the food',
  ],
};

String _categoryDirection(MealFoodCategory category) => switch (category) {
  MealFoodCategory.breadGrain =>
    'show crumb, grain or layered texture clearly; warm bakery highlights',
  MealFoodCategory.moroccanDish =>
    'authentic Moroccan plating cues, restrained ceramic detail only when essential to recognition',
  MealFoodCategory.gulfDish =>
    'authentic Gulf presentation cues, rice and protein separation visible when relevant',
  MealFoodCategory.meatPoultry =>
    'clean cooked-food presentation, realistic browning, no raw-meat aesthetic unless concept explicitly requires it',
  MealFoodCategory.fishSeafood =>
    'clean fresh or cooked seafood presentation, species silhouette readable at small size',
  MealFoodCategory.egg =>
    'simple preparation-specific form, bright natural whites and yolk',
  MealFoodCategory.dairy =>
    'clean creamy texture and vessel only when needed for recognition',
  MealFoodCategory.legume =>
    'show whole legumes or recognizable cooked texture, avoid generic brown puree',
  MealFoodCategory.vegetable =>
    'fresh natural form, crisp surface detail, no decorative garnish',
  MealFoodCategory.fruit =>
    'fresh natural form, one whole unit plus a minimal cut face only when useful',
  MealFoodCategory.nutSeed =>
    'macro-realistic natural texture, compact centered cluster',
  MealFoodCategory.fatSauce =>
    'small elegant vessel only when required, ingredient identity remains primary',
  MealFoodCategory.drink =>
    'single clean glass or culturally correct cup, liquid color and texture clearly visible',
  MealFoodCategory.sweetDessert =>
    'premium patisserie rendering, accurate local geometry, restrained highlights',
  MealFoodCategory.snackFastFood =>
    'single recognizable serving, editorial rather than advertising style',
  MealFoodCategory.saladMeal =>
    'top ingredients readable, compact bowl composition, no excessive garnish',
  MealFoodCategory.soup =>
    'single bowl, texture and principal ingredients visible, no steam covering the food',
  MealFoodCategory.other =>
    'prioritize immediate recognition and natural food texture',
};

Map<String, Object> _entry(MealFoodItem item) => <String, Object>{
  'id': item.id,
  'asset': 'assets/food/pictograms/v1/${item.pictogramKey}.webp',
  'label_fr': item.fr,
  'label_en': item.en,
  'label_ar': item.ar,
  'category': item.category.name,
  'regions': item.regions.map((region) => region.name).toList(growable: false),
  'prompt': <String>[
    'Create one premium IAMINA food pictogram for ${item.en}.',
    _style['material']! as String,
    _style['camera']! as String,
    _style['lighting']! as String,
    _style['composition']! as String,
    _categoryDirection(item.category),
    'Transparent background. No text, no logo, no watermark.',
  ].join(' '),
};

void main() {
  final ids = mealFoodCatalog.map((item) => item.id).toSet();
  if (ids.length != mealFoodCatalog.length) {
    throw StateError('Duplicate food IDs prevent a deterministic asset manifest.');
  }
  if (mealFoodCatalog.any((item) => item.visual == '🍽️')) {
    throw StateError('Generic food visuals must be resolved before pictogram generation.');
  }

  final manifest = <String, Object>{
    'style': _style,
    'catalog_version': mealFoodCatalogVersion,
    'count': mealFoodCatalog.length,
    'items': mealFoodCatalog.map(_entry).toList(growable: false),
  };
  print(const JsonEncoder.withIndent('  ').convert(manifest));
}
