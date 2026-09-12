import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../core/data/meal_food_catalog.dart';

abstract class MealFoodFavoritesRepository {
  Future<Set<String>> load();

  Future<void> save(Set<String> ids);
}

class SecureMealFoodFavoritesRepository implements MealFoodFavoritesRepository {
  static const String storageKey = 'iamina.meal_food_favorites.v1';

  final FlutterSecureStorage _storage;

  const SecureMealFoodFavoritesRepository({
    FlutterSecureStorage storage = const FlutterSecureStorage(),
  }) : _storage = storage;

  @override
  Future<Set<String>> load() async {
    final raw = await _storage.read(key: storageKey);
    if (raw == null || raw.trim().isEmpty) return <String>{};
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return <String>{};
      return decoded
          .whereType<String>()
          .where((id) => mealFoodById(id) != null)
          .toSet();
    } catch (_) {
      return <String>{};
    }
  }

  @override
  Future<void> save(Set<String> ids) async {
    final valid = ids.where((id) => mealFoodById(id) != null).toList()..sort();
    await _storage.write(key: storageKey, value: jsonEncode(valid));
  }
}
