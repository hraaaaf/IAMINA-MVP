import 'dart:convert';
import 'package:flutter/widgets.dart';

class MealFoodItem {
  final String id;
  final String fr;
  final String en;
  final String ar;
  final List<String> aliases;

  const MealFoodItem(
    this.id,
    this.fr,
    this.en,
    this.ar, [
    this.aliases = const [],
  ]);

  String labelFor(Locale locale) {
    if (locale.languageCode == 'ar') return ar;
    if (locale.languageCode == 'en') return en;
    return fr;
  }

  String get searchable => <String>[id, fr, en, ar, ...aliases].join(' ');
}

const List<MealFoodItem> mealFoodCatalog = <MealFoodItem>[
  MealFoodItem(
    'moroccan_bread',
    'Pain marocain',
    'Moroccan bread',
    'خبز مغربي',
    ['khobz', 'خبز'],
  ),
  MealFoodItem(
    'whole_grain_bread',
    'Pain complet',
    'Whole-grain bread',
    'خبز كامل الحبوب',
    ['pain', 'bread'],
  ),
  MealFoodItem('msemen', 'Msemen', 'Msemen', 'مسمن'),
  MealFoodItem('baghrir', 'Baghrir', 'Baghrir', 'بغرير'),
  MealFoodItem('harcha', 'Harcha', 'Harcha', 'حرشة'),
  MealFoodItem('couscous', 'Couscous', 'Couscous', 'كسكس', ['كسكسي']),
  MealFoodItem('tajine', 'Tajine', 'Tagine', 'طاجين'),
  MealFoodItem('harira', 'Harira', 'Harira soup', 'حريرة'),
  MealFoodItem('bissara', 'Bissara', 'Bissara', 'بيصارة', ['bayssara']),
  MealFoodItem('lentils', 'Lentilles', 'Lentils', 'عدس'),
  MealFoodItem('chickpeas', 'Pois chiches', 'Chickpeas', 'حمص'),
  MealFoodItem('white_beans', 'Haricots blancs', 'White beans', 'لوبيا بيضاء', [
    'loubia',
  ]),
  MealFoodItem('rice', 'Riz', 'Rice', 'أرز'),
  MealFoodItem('pasta', 'Pâtes', 'Pasta', 'معكرونة'),
  MealFoodItem('potato', 'Pomme de terre', 'Potato', 'بطاطس'),
  MealFoodItem('vegetables', 'Légumes', 'Vegetables', 'خضروات', ['légume']),
  MealFoodItem('salad', 'Salade', 'Salad', 'سلطة'),
  MealFoodItem('tomato', 'Tomate', 'Tomato', 'طماطم'),
  MealFoodItem('carrot', 'Carotte', 'Carrot', 'جزر'),
  MealFoodItem('zucchini', 'Courgette', 'Zucchini', 'كوسة'),
  MealFoodItem('egg', 'Œuf', 'Egg', 'بيض', ['oeuf', 'œufs', 'eggs']),
  MealFoodItem('chicken', 'Poulet', 'Chicken', 'دجاج'),
  MealFoodItem('beef', 'Bœuf', 'Beef', 'لحم بقري', ['boeuf']),
  MealFoodItem('lamb', 'Agneau', 'Lamb', 'لحم غنم'),
  MealFoodItem('fish', 'Poisson', 'Fish', 'سمك'),
  MealFoodItem('sardines', 'Sardines', 'Sardines', 'سردين'),
  MealFoodItem('tuna', 'Thon', 'Tuna', 'تونة'),
  MealFoodItem('yogurt', 'Yaourt', 'Yogurt', 'زبادي', ['yoghurt']),
  MealFoodItem('cheese', 'Fromage', 'Cheese', 'جبن'),
  MealFoodItem('milk', 'Lait', 'Milk', 'حليب'),
  MealFoodItem('oats', 'Flocons d’avoine', 'Oats', 'شوفان', ['avoine']),
  MealFoodItem('cereal', 'Céréales', 'Cereal', 'حبوب الإفطار'),
  MealFoodItem('dates', 'Dattes', 'Dates', 'تمر'),
  MealFoodItem('apple', 'Pomme', 'Apple', 'تفاح'),
  MealFoodItem('banana', 'Banane', 'Banana', 'موز'),
  MealFoodItem('orange', 'Orange', 'Orange', 'برتقال'),
  MealFoodItem('pear', 'Poire', 'Pear', 'كمثرى'),
  MealFoodItem('avocado', 'Avocat', 'Avocado', 'أفوكادو'),
  MealFoodItem('almonds', 'Amandes', 'Almonds', 'لوز'),
  MealFoodItem('olives', 'Olives', 'Olives', 'زيتون'),
  MealFoodItem('amlou', 'Amlou', 'Amlou', 'أملو'),
  MealFoodItem('mint_tea', 'Thé à la menthe', 'Mint tea', 'شاي بالنعناع', [
    'thé',
    'tea',
  ]),
  MealFoodItem('coffee', 'Café', 'Coffee', 'قهوة'),
  MealFoodItem('water', 'Eau', 'Water', 'ماء'),
  MealFoodItem('juice', 'Jus', 'Juice', 'عصير'),
  MealFoodItem('soup', 'Soupe', 'Soup', 'شوربة'),
  MealFoodItem('sandwich', 'Sandwich', 'Sandwich', 'ساندويتش'),
  MealFoodItem('pizza', 'Pizza', 'Pizza', 'بيتزا'),
  MealFoodItem('croissant', 'Croissant', 'Croissant', 'كرواسون'),
];

final Map<String, MealFoodItem> _mealFoodById = <String, MealFoodItem>{
  for (final item in mealFoodCatalog) item.id: item,
};

MealFoodItem? mealFoodById(String id) => _mealFoodById[id];

List<String> decodeMealItemIds(String? raw) {
  if (raw == null || raw.trim().isEmpty) return const <String>[];
  try {
    final decoded = jsonDecode(raw);
    if (decoded is! List) return const <String>[];
    return decoded
        .whereType<String>()
        .where(_mealFoodById.containsKey)
        .toList(growable: false);
  } catch (_) {
    return const <String>[];
  }
}

String encodeMealItemIds(Iterable<String> ids) => jsonEncode(
  ids.where(_mealFoodById.containsKey).toSet().toList(growable: false),
);

String foldMealText(String value) => value
    .toLowerCase()
    .replaceAll('œ', 'oe')
    .replaceAll(RegExp('[àáâäãå]'), 'a')
    .replaceAll(RegExp('[ç]'), 'c')
    .replaceAll(RegExp('[èéêë]'), 'e')
    .replaceAll(RegExp('[ìíîï]'), 'i')
    .replaceAll(RegExp('[ñ]'), 'n')
    .replaceAll(RegExp('[òóôöõ]'), 'o')
    .replaceAll(RegExp('[ùúûü]'), 'u')
    .replaceAll(RegExp('[ýÿ]'), 'y')
    .replaceAll(RegExp(r'[^a-z0-9\u0600-\u06ff]+'), ' ')
    .trim();

List<MealFoodItem> searchMealFoods(String query, {int limit = 12}) {
  final folded = foldMealText(query);
  if (folded.length < 2) return const <MealFoodItem>[];
  return mealFoodCatalog
      .where((item) => foldMealText(item.searchable).contains(folded))
      .take(limit)
      .toList(growable: false);
}

List<MealFoodItem> matchRecognizedMealFoods(Iterable<String> recognized) {
  final found = <String, MealFoodItem>{};
  for (final raw in recognized) {
    final needle = foldMealText(raw);
    if (needle.isEmpty) continue;
    MealFoodItem? match;
    for (final item in mealFoodCatalog) {
      final french = foldMealText(item.fr);
      if (french == needle ||
          french.contains(needle) ||
          needle.contains(french)) {
        match = item;
        break;
      }
    }
    if (match == null) {
      final needleTokens = needle
          .split(' ')
          .where((e) => e.length >= 3)
          .toSet();
      int best = 0;
      for (final item in mealFoodCatalog) {
        final tokens = foldMealText(item.fr).split(' ').toSet();
        final score = needleTokens.intersection(tokens).length;
        if (score > best) {
          best = score;
          match = item;
        }
      }
      if (best == 0) match = null;
    }
    if (match != null) found[match.id] = match;
  }
  return found.values.take(8).toList(growable: false);
}
