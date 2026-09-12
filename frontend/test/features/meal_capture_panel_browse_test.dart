import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/widgets/meal_capture_panel.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/meal_food_favorites_repository.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class _EmptyFavoritesRepository implements MealFoodFavoritesRepository {
  @override
  Future<Set<String>> load() async => <String>{};

  @override
  Future<void> save(Set<String> ids) async {}
}

Finder _searchRows() => find.byWidgetPredicate((widget) {
  final key = widget.key;
  return key is ValueKey<String> && key.value.startsWith('meal-search-');
});

void main() {
  late AppDatabase db;

  setUp(() => db = AppDatabase(NativeDatabase.memory()));
  tearDown(() async => db.close());

  Widget harness() => MaterialApp(
    locale: const Locale('fr'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(
      body: Provider<AppDatabase>.value(
        value: db,
        child: SingleChildScrollView(
          child: MealCapturePanel(
            selectedIds: const <String>[],
            onChanged: (_) {},
            canUsePhotoRecognition: false,
            favoritesRepository: _EmptyFavoritesRepository(),
          ),
        ),
      ),
    ),
  );

  testWidgets('All is an explicit exhaustive browse with progressive disclosure', (
    tester,
  ) async {
    await tester.pumpWidget(harness());
    await tester.pumpAndSettle();

    expect(_searchRows(), findsNothing);
    expect(find.byKey(const Key('meal-results-more')), findsNothing);

    await tester.tap(find.byKey(const Key('meal-category-all')));
    await tester.pumpAndSettle();

    expect(_searchRows(), findsNWidgets(24));
    expect(find.byKey(const Key('meal-results-more')), findsOneWidget);

    await tester.ensureVisible(find.byKey(const Key('meal-results-more')));
    await tester.tap(find.byKey(const Key('meal-results-more')));
    await tester.pumpAndSettle();

    expect(_searchRows(), findsNWidgets(48));
  });
}
