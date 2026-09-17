import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:drift/native.dart';
import 'package:frontend/core/data/app_database.dart';
import 'package:frontend/core/data/meal_food_catalog_v3.dart';
import 'package:frontend/features/journal/widgets/meal_capture_panel.dart';
import 'package:frontend/features/journal/services/meal_photo_recognition.dart';
import 'package:frontend/features/journal/data/meal_food_favorites_repository.dart';
import 'package:frontend/l10n/app_localizations.dart';

void main() {
  late AppDatabase db;
  setUp(() => db = AppDatabase(NativeDatabase.memory()));
  tearDown(() async => db.close());
  Widget harness({Locale locale = const Locale('fr'),required List<String> selected,required ValueChanged<List<String>> onChanged,MealPhotoRecognition? photoRecognition,bool canUsePhoto = true,MealFoodFavoritesRepository? favoritesRepository,}) => MaterialApp(locale:locale,localizationsDelegates:AppLocalizations.localizationsDelegates,supportedLocales:AppLocalizations.supportedLocales,home:Scaffold(body:Provider<AppDatabase>.value(value:db,child:SingleChildScrollView(child:MealCapturePanel(selectedIds:selected,onChanged:onChanged,canUsePhotoRecognition:canUsePhoto,photoRecognition:photoRecognition,favoritesRepository:favoritesRepository)))));

  test('catalog v3 is broad, unique and Morocco + GCC aware', () {
    expect(mealFoodCatalogVersion, '3.8.0-algeria-depth-b22');
    expect(mealFoodCatalog.length, greaterThanOrEqualTo(300));
    final ids = mealFoodCatalog.map((item) => item.id).toSet();
    expect(ids.length, mealFoodCatalog.length, reason: 'Duplicate food IDs');
    final morocco = mealFoodsForRegion(MealFoodRegion.morocco); final gulf = mealFoodsForRegion(MealFoodRegion.gulf); final universal = mealFoodsForRegion(MealFoodRegion.universal);
    expect(morocco.length, greaterThanOrEqualTo(40)); expect(gulf.length, greaterThanOrEqualTo(60)); expect(universal.length, greaterThanOrEqualTo(180));
  });
}
