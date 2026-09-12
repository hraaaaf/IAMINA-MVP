import 'dart:convert';

import 'package:amina/core/data/meal_food_catalog.dart';

const int _batchSize = 24;

const _style = <String, Object>{
  'brand': 'IAMINA',
  'version': 'food-pictogram-v1',
  'master_size': 1024,
  'runtime_size': 256,
  'aspect_ratio': '1:1',
  'background': 'transparent',
  'camera': 'three-quarter top-down, consistent 38 degree angle',
  'lighting':
      'soft premium studio light, gentle teal bounce, warm natural highlights',
  'material':
      'realistic food illustration with refined editorial finish, not cartoon, not emoji',
  'composition':
      'single food concept centered, 72 percent frame occupancy, subtle contact shadow',
  'accessibility':
      'must remain identifiable at 48 px without relying on text or color alone',
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

/// First 48 concepts establish the visual language before the long-tail batch.
/// The order intentionally mixes universal, Moroccan and Gulf foods so a bad
/// art direction is caught before hundreds of assets inherit it.
const List<String> _launchPriorityIds = <String>[
  'egg',
  'whole_grain_bread',
  'chicken',
  'grilled_chicken',
  'beef',
  'sardines',
  'salmon',
  'milk',
  'plain_yogurt',
  'apple',
  'banana',
  'orange',
  'tomato',
  'potato',
  'lentils',
  'chickpeas',
  'olive_oil',
  'pizza',
  'burger',
  'moroccan_bread',
  'msemen',
  'baghrir',
  'couscous_7_vegetables',
  'harira',
  'rfissa',
  'chicken_preserved_lemon_tagine',
  'kefta_tagine',
  'zaalouk',
  'taktouka',
  'amlou',
  'mint_tea',
  'moroccan_sweet_tea',
  'arabic_flatbread',
  'tannour_bread',
  'machboos_chicken',
  'kabsa_chicken',
  'mandi_chicken',
  'harees',
  'jareesh',
  'thareed',
  'balaleet',
  'luqaimat',
  'dates',
  'ajwa_dates',
  'arabic_coffee',
  'karak_tea',
  'shawarma_chicken',
  'hummus',
];

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

List<MealFoodItem> _orderedItems() {
  final byId = <String, MealFoodItem>{
    for (final item in mealFoodCatalog) item.id: item,
  };
  final missingPriority = _launchPriorityIds
      .where((id) => !byId.containsKey(id))
      .toList(growable: false);
  if (missingPriority.isNotEmpty) {
    throw StateError(
      'Pictogram launch priority references missing food IDs: '
      '${missingPriority.join(', ')}',
    );
  }

  final priority = _launchPriorityIds.map((id) => byId[id]!).toList();
  final prioritySet = _launchPriorityIds.toSet();
  final remaining = mealFoodCatalog
      .where((item) => !prioritySet.contains(item.id))
      .toList(growable: true)
    ..sort((a, b) {
      final byCategory = a.category.index.compareTo(b.category.index);
      if (byCategory != 0) return byCategory;
      return a.fr.compareTo(b.fr);
    });
  return <MealFoodItem>[...priority, ...remaining];
}

Map<String, Object> _entry(MealFoodItem item, int index) => <String, Object>{
  'id': item.id,
  'asset': 'assets/food/pictograms/v1/${item.pictogramKey}.webp',
  'label_fr': item.fr,
  'label_en': item.en,
  'label_ar': item.ar,
  'category': item.category.name,
  'regions': item.regions.map((region) => region.name).toList(growable: false),
  'priority': index < _launchPriorityIds.length ? 'launch' : 'catalog',
  'batch': (index ~/ _batchSize) + 1,
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

int? _requestedBatch(List<String> args, int batchCount) {
  final batchArgs = args.where((arg) => arg.startsWith('--batch=')).toList();
  if (batchArgs.length > 1) {
    throw ArgumentError('Use at most one --batch=N selector.');
  }
  if (batchArgs.isEmpty) return null;

  final raw = batchArgs.single.substring('--batch='.length);
  final batch = int.tryParse(raw);
  if (batch == null || batch < 1 || batch > batchCount) {
    throw ArgumentError.value(raw, '--batch', 'Expected 1..$batchCount');
  }
  return batch;
}

void main(List<String> args) {
  final unsupported = args
      .where((arg) => !arg.startsWith('--batch='))
      .toList(growable: false);
  if (unsupported.isNotEmpty) {
    throw ArgumentError('Unsupported arguments: ${unsupported.join(', ')}');
  }

  final ids = mealFoodCatalog.map((item) => item.id).toSet();
  if (ids.length != mealFoodCatalog.length) {
    throw StateError(
      'Duplicate food IDs prevent a deterministic asset manifest.',
    );
  }
  if (mealFoodCatalog.any((item) => item.visual == '🍽️')) {
    throw StateError(
      'Generic food visuals must be resolved before pictogram generation.',
    );
  }

  final ordered = _orderedItems();
  final batchCount = (ordered.length / _batchSize).ceil();
  final requestedBatch = _requestedBatch(args, batchCount);
  final indexed = <({int index, MealFoodItem item})>[
    for (var index = 0; index < ordered.length; index++)
      (index: index, item: ordered[index]),
  ];
  final selected = requestedBatch == null
      ? indexed
      : indexed
          .where((entry) => (entry.index ~/ _batchSize) + 1 == requestedBatch)
          .toList(growable: false);

  final manifest = <String, Object?>{
    'style': _style,
    'catalog_version': mealFoodCatalogVersion,
    'catalog_count': mealFoodCatalog.length,
    'selected_count': selected.length,
    'batch_size': _batchSize,
    'launch_count': _launchPriorityIds.length,
    'batch_count': batchCount,
    'selected_batch': requestedBatch,
    'items': <Map<String, Object>>[
      for (final entry in selected) _entry(entry.item, entry.index),
    ],
  };
  print(const JsonEncoder.withIndent('  ').convert(manifest));
}
