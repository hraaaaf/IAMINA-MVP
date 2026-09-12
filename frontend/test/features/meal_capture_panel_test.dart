import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/ai_models.dart';
import 'package:amina/features/journal/widgets/meal_capture_panel.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/meal_food_favorites_repository.dart';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class _MemoryFavoritesRepository implements MealFoodFavoritesRepository {
  Set<String> ids;

  _MemoryFavoritesRepository([Set<String>? initial])
    : ids = <String>{...?initial};

  @override
  Future<Set<String>> load() async => Set<String>.from(ids);

  @override
  Future<void> save(Set<String> ids) async {
    this.ids = Set<String>.from(ids);
  }
}

void main() {
  late AppDatabase db;
  setUp(() => db = AppDatabase(NativeDatabase.memory()));
  tearDown(() async => db.close());

  Widget harness({
    Locale locale = const Locale('fr'),
    required List<String> selected,
    required ValueChanged<List<String>> onChanged,
    MealPhotoRecognition? photoRecognition,
    bool canUsePhoto = true,
    MealFoodFavoritesRepository? favoritesRepository,
  }) {
    return MaterialApp(
      locale: locale,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(
        body: Provider<AppDatabase>.value(
          value: db,
          child: SingleChildScrollView(
            child: MealCapturePanel(
              selectedIds: selected,
              onChanged: onChanged,
              canUsePhotoRecognition: canUsePhoto,
              photoRecognition: photoRecognition,
              favoritesRepository: favoritesRepository,
            ),
          ),
        ),
      ),
    );
  }

  test('catalog v3 is broad, unique and Morocco + GCC aware', () {
    expect(mealFoodCatalogVersion, '3.0.0-morocco-gcc');
    expect(mealFoodCatalog.length, greaterThanOrEqualTo(300));

    final ids = mealFoodCatalog.map((item) => item.id).toSet();
    expect(ids.length, mealFoodCatalog.length, reason: 'Duplicate food IDs');

    final morocco = mealFoodsForRegion(MealFoodRegion.morocco);
    final gulf = mealFoodsForRegion(MealFoodRegion.gulf);
    final universal = mealFoodsForRegion(MealFoodRegion.universal);
    expect(morocco.length, greaterThanOrEqualTo(40));
    expect(gulf.length, greaterThanOrEqualTo(60));
    expect(universal.length, greaterThanOrEqualTo(180));

    expect(mealFoodById('couscous_7_vegetables'), isNotNull);
    expect(mealFoodById('rfissa'), isNotNull);
    expect(mealFoodById('machboos_chicken'), isNotNull);
    expect(mealFoodById('harees'), isNotNull);
    expect(mealFoodById('balaleet'), isNotNull);
    expect(mealFoodById('karak_tea'), isNotNull);
  });

  test('regional and multilingual search ranks exact concepts first', () {
    expect(searchMealFoods('rfissa').first.id, 'rfissa');
    expect(searchMealFoods('machboos').first.id, startsWith('machboos_'));
    expect(searchMealFoods('بيض').first.id, 'egg');
    expect(searchMealFoods('oeuf').first.id, 'egg');
    expect(
      searchMealFoods('kabsa').map((item) => item.id),
      contains('kabsa_chicken'),
    );
    expect(
      searchMealFoods('شاورما').map((item) => item.id),
      contains('shawarma_chicken'),
    );
  });

  test('every food has a non-generic visual cue and keeps a text label', () {
    for (final item in mealFoodCatalog) {
      expect(item.visual, isNot('🍽️'), reason: 'Missing visual for ${item.id}');
      expect(item.visual.trim(), isNotEmpty, reason: 'Empty visual for ${item.id}');
      expect(item.pictogramKey, item.id);
      for (final locale in const <Locale>[
        Locale('fr'),
        Locale('en'),
        Locale('ar'),
      ]) {
        final plain = item.plainLabelFor(locale);
        final visual = item.labelFor(locale);
        expect(plain.trim(), isNotEmpty, reason: 'Missing text for ${item.id}');
        expect(visual, startsWith('${item.visual} '));
        expect(visual, contains(plain));
      }
    }
  });

  testWidgets(
    'photo proposal never becomes meal data before explicit confirmation',
    (tester) async {
      var selected = <String>[];
      Future<MealAnalysisResult?> recognition() async =>
          const MealAnalysisResult(
            foods: <String>['pain complet', 'œuf'],
            confidence: 'high',
            fallback: false,
          );

      await tester.pumpWidget(
        harness(
          selected: selected,
          onChanged: (value) => selected = value,
          photoRecognition: recognition,
          favoritesRepository: _MemoryFavoritesRepository(),
        ),
      );
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byKey(const Key('meal-photo-button')));
      await tester.tap(find.byKey(const Key('meal-photo-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('meal-photo-proposal')), findsOneWidget);
      expect(selected, isEmpty);
      await tester.tap(
        find.byKey(const Key('meal-photo-candidate-whole_grain_bread')),
      );
      await tester.pump();
      expect(selected, isEmpty);
      await tester.tap(find.byKey(const Key('meal-photo-confirm')));
      await tester.pumpAndSettle();
      expect(selected, contains('whole_grain_bread'));
    },
  );

  testWidgets('Arabic search uses Arabic food labels and RTL', (tester) async {
    var selected = <String>[];
    await tester.pumpWidget(
      harness(
        locale: const Locale('ar'),
        selected: selected,
        onChanged: (value) => selected = value,
        favoritesRepository: _MemoryFavoritesRepository(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('meal-food-search')), 'بيض');
    await tester.pump();
    final result = find.byKey(const Key('meal-search-egg'));
    expect(result, findsOneWidget);
    expect(Directionality.of(tester.element(result)), TextDirection.rtl);
    expect(find.text('بيض'), findsOneWidget);
    expect(find.text('Œuf'), findsNothing);
  });

  testWidgets(
    'first use hides empty history and keeps capture actions immediately available',
    (tester) async {
      await tester.pumpWidget(
        harness(
          selected: const <String>[],
          onChanged: (_) {},
          favoritesRepository: _MemoryFavoritesRepository(),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Récents'), findsNothing);
      expect(find.text('Habituels'), findsNothing);
      expect(find.byKey(const Key('meal-food-search')), findsOneWidget);
      expect(find.byKey(const Key('meal-category-rail')), findsOneWidget);
      expect(find.byKey(const Key('meal-photo-button')), findsOneWidget);
    },
  );

  testWidgets('Gulf category browses regional dishes without typing', (
    tester,
  ) async {
    await tester.pumpWidget(
      harness(
        selected: const <String>[],
        onChanged: (_) {},
        favoritesRepository: _MemoryFavoritesRepository(),
      ),
    );
    await tester.pumpAndSettle();

    final rail = find.byKey(const Key('meal-category-rail'));
    await tester.drag(rail, const Offset(-500, 0));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('meal-category-gulfDish')));
    await tester.pumpAndSettle();

    expect(find.text('Harees'), findsWidgets);
    expect(find.text('Cuisine du Golfe'), findsWidgets);
    expect(find.byKey(const Key('meal-search-rfissa')), findsNothing);
  });

  testWidgets(
    'recent and habitual foods come only from confirmed structured history',
    (tester) async {
      for (var i = 0; i < 3; i++) {
        await db
            .into(db.logEntries)
            .insert(
              LogEntriesCompanion.insert(
                createdAt: DateTime(2026, 8, 9, 8 + i),
                bloodSugar: 120.0 + i,
                clientUuid: '88888888-8888-8888-8888-88888888888$i',
                mealItemsJson: const Value('["egg","moroccan_bread"]'),
                loggedAt: Value(DateTime(2026, 8, 9, 8 + i)),
              ),
            );
      }
      await tester.pumpWidget(
        harness(
          selected: const <String>[],
          onChanged: (_) {},
          favoritesRepository: _MemoryFavoritesRepository(),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Récents'), findsOneWidget);
      expect(find.text('Habituels'), findsOneWidget);
      expect(find.text('Œuf'), findsWidgets);
      expect(find.text('Pain marocain'), findsWidgets);
    },
  );

  testWidgets('search result selects food and collapses active results', (
    tester,
  ) async {
    var selected = <String>[];
    await tester.pumpWidget(
      harness(
        selected: selected,
        onChanged: (value) => selected = value,
        favoritesRepository: _MemoryFavoritesRepository(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('meal-food-search')), 'oeuf');
    await tester.pump();
    final result = find.byKey(const Key('meal-search-egg'));
    expect(result, findsOneWidget);
    expect(find.text('Œuf'), findsOneWidget);
    await tester.tap(result);
    await tester.pump();

    expect(selected, contains('egg'));
    expect(find.byKey(const Key('meal-search-egg')), findsNothing);
    expect(find.byKey(const Key('meal-food-search-clear')), findsNothing);
    expect(find.byKey(const Key('meal-category-rail')), findsNothing);
    final field = tester.widget<TextField>(
      find.byKey(const Key('meal-food-search')),
    );
    expect(field.controller?.text, isEmpty);
  });

  testWidgets('favorite can be added from search and surfaces in quick access', (
    tester,
  ) async {
    final favorites = _MemoryFavoritesRepository();
    await tester.pumpWidget(
      harness(
        selected: const <String>[],
        onChanged: (_) {},
        favoritesRepository: favorites,
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('meal-food-search')), 'oeuf');
    await tester.pump();
    await tester.tap(find.byKey(const Key('meal-favorite-egg')));
    await tester.pumpAndSettle();
    expect(favorites.ids, contains('egg'));

    await tester.tap(find.byKey(const Key('meal-food-search-clear')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('meal-favorites-section')), findsOneWidget);
    expect(find.byKey(const Key('meal-favorite-row-egg')), findsOneWidget);
  });

  testWidgets('favorite quick access can remove a stored favorite', (
    tester,
  ) async {
    final favorites = _MemoryFavoritesRepository(<String>{'whole_grain_bread'});
    await tester.pumpWidget(
      harness(
        selected: const <String>[],
        onChanged: (_) {},
        favoritesRepository: favorites,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('meal-favorites-section')), findsOneWidget);
    expect(
      find.byKey(const Key('meal-favorite-row-whole_grain_bread')),
      findsOneWidget,
    );
    await tester.tap(
      find.byKey(const Key('meal-favorite-whole_grain_bread')),
    );
    await tester.pumpAndSettle();
    expect(favorites.ids, isNot(contains('whole_grain_bread')));
    expect(find.byKey(const Key('meal-favorites-section')), findsNothing);
  });
}
