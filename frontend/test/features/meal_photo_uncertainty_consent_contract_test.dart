import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/ai_models.dart';
import 'package:amina/features/journal/widgets/meal_capture_panel.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/meal_food_favorites_repository.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class _NoFavorites implements MealFoodFavoritesRepository {
  @override Future<Set<String>> load() async => <String>{};
  @override Future<void> save(Set<String> ids) async {}
}

void main() {
  late AppDatabase db;
  setUp(() => db = AppDatabase(NativeDatabase.memory()));
  tearDown(() async => db.close());

  Widget app({
    required ValueChanged<List<String>> onChanged,
    required MealPhotoRecognition recognize,
    required bool permitted,
  }) => MaterialApp(
    locale: const Locale('fr'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(body: Provider<AppDatabase>.value(
      value: db,
      child: SingleChildScrollView(child: MealCapturePanel(
        selectedIds: const <String>[],
        onChanged: onChanged,
        canUsePhotoRecognition: permitted,
        photoRecognition: recognize,
        favoritesRepository: _NoFavorites(),
      )),
    )),
  );

  testWidgets('decision #14 denied consent never calls recognition', (tester) async {
    var calls = 0;
    var selection = <String>[];
    await tester.pumpWidget(app(
      permitted: false,
      onChanged: (value) => selection = value,
      recognize: () async {
        calls++;
        return const MealAnalysisResult(
          foods: ['pain complet'], confidence: 'high', fallback: false,
        );
      },
    ));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('meal-photo-button')));
    await tester.tap(find.byKey(const Key('meal-photo-button')));
    await tester.pumpAndSettle();
    expect(calls, 0);
    expect(selection, isEmpty);
    expect(find.byKey(const Key('meal-photo-proposal')), findsNothing);
  });

  testWidgets('decision #14 uncertain recognition cannot auto-add foods', (tester) async {
    var selection = <String>[];
    await tester.pumpWidget(app(
      permitted: true,
      onChanged: (value) => selection = value,
      recognize: () async => const MealAnalysisResult(
        foods: ['pain complet'], confidence: 'low', fallback: false,
      ),
    ));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('meal-photo-button')));
    await tester.tap(find.byKey(const Key('meal-photo-button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('meal-photo-proposal')), findsOneWidget);
    expect(selection, isEmpty);
    expect(tester.widget<FilledButton>(
      find.byKey(const Key('meal-photo-confirm')),
    ).onPressed, isNull);
    await tester.tap(find.byKey(const Key('meal-photo-candidate-whole_grain_bread')));
    await tester.pump();
    expect(selection, isEmpty);
    await tester.tap(find.byKey(const Key('meal-photo-confirm')));
    await tester.pumpAndSettle();
    expect(selection, contains('whole_grain_bread'));
  });

  testWidgets('decision #14 fallback leaves manual meal search available', (tester) async {
    var selection = <String>[];
    await tester.pumpWidget(app(
      permitted: true,
      onChanged: (value) => selection = value,
      recognize: () async => const MealAnalysisResult(
        foods: ['pain complet'], confidence: 'low', fallback: true,
      ),
    ));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('meal-photo-button')));
    await tester.tap(find.byKey(const Key('meal-photo-button')));
    await tester.pumpAndSettle();
    expect(selection, isEmpty);
    expect(find.byKey(const Key('meal-photo-proposal')), findsNothing);
    expect(find.byKey(const Key('meal-food-search')), findsOneWidget);
  });
}
