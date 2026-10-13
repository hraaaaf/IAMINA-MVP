import 'dart:io';

import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/core/data/nutrition_catalog.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/ai_models.dart';
import 'package:amina/features/journal/widgets/meal_capture_panel.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/meal_food_favorites_repository.dart';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class _MemoryFavorites implements MealFoodFavoritesRepository {
  @override
  Future<Set<String>> load() async => <String>{};
  @override
  Future<void> save(Set<String> ids) async {}
}

Widget _harness({
  required AppDatabase db,
  required List<String> selected,
  required ValueChanged<List<String>> changed,
  required MealPhotoRecognition recognize,
  bool permission = true,
}) => MaterialApp(
  locale: const Locale('fr'),
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(
    body: Provider<AppDatabase>.value(
      value: db,
      child: SingleChildScrollView(
        child: MealCapturePanel(
          selectedIds: selected,
          onChanged: changed,
          canUsePhotoRecognition: permission,
          photoRecognition: recognize,
          favoritesRepository: _MemoryFavorites(),
        ),
      ),
    ),
  ),
);

void main() {
  testWidgets(
    'decision #15 keeps manual selection until confirmed photo, then one Drift entry',
    (tester) async {
      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      var selected = <String>['egg'];
      await tester.pumpWidget(_harness(
        db: db,
        selected: selected,
        changed: (items) => selected = items,
        recognize: () async => const MealAnalysisResult(
          foods: ['pain complet'], confidence: 'high', fallback: false,
        ),
      ));
      await tester.pumpAndSettle();
      final photo = find.byKey(const Key('meal-photo-button'));
      await tester.ensureVisible(photo);
      await tester.tap(photo);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('meal-photo-proposal')), findsOneWidget);
      expect(selected, ['egg']); // Still uncommitted.
      expect(await db.select(db.logEntries).get(), isEmpty);

      final candidate = find.byKey(
        const Key('meal-photo-candidate-whole_grain_bread'),
      );
      await tester.ensureVisible(candidate);
      await tester.tap(candidate);
      await tester.pump();
      expect(selected, ['egg']); // Preview selection isn't a meal log.
      final confirm = find.byKey(const Key('meal-photo-confirm'));
      await tester.ensureVisible(confirm);
      await tester.tap(confirm);
      await tester.pumpAndSettle();
      expect(selected.toSet(), {'egg', 'whole_grain_bread'});
      expect(await db.select(db.logEntries).get(), isEmpty);

      // Mirrors the production AddLogSheet's single local insert schema, with
      // synthetic note + user-entered grams, not a clinical carb inference.
      const note = 'Œuf et pain / بيض وخبز, synthetic';
      final items = encodeMealItemIds(selected);
      final portions = encodeMealPortionSelections([
        const MealPortionSelection(foodId: 'whole_grain_bread', grams: 75),
      ]);
      await db.into(db.logEntries).insert(LogEntriesCompanion.insert(
        createdAt: DateTime.utc(2026, 10, 13, 8),
        bloodSugar: 120.0,
        clientUuid: '15151515-1515-4151-8151-151515151515',
        mealDescription: const Value(note),
        mealItemsJson: Value(items),
        mealPortionsJson: Value(portions),
      ));
      final rows = await db.select(db.logEntries).get();
      expect(rows, hasLength(1));
      expect(rows.single.mealDescription, note);
      expect(decodeMealItemIds(rows.single.mealItemsJson).toSet(),
          {'egg', 'whole_grain_bread'});
      final portionsBack = decodeMealPortionSelections(
        rows.single.mealPortionsJson,
      );
      expect(portionsBack, hasLength(1));
      expect(portionsBack.single.foodId, 'whole_grain_bread');
      expect(portionsBack.single.grams, 75.0);
      expect(rows.single.insulinUnits, isNull);
    },
  );

  testWidgets('uncertain fallback photo cannot change the existing manual draft', (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    var selected = <String>['egg'];
    await tester.pumpWidget(_harness(
      db: db,
      selected: selected,
      changed: (items) => selected = items,
      recognize: () async => const MealAnalysisResult(
        foods: ['pain complet'], confidence: 'low', fallback: true,
      ),
    ));
    await tester.pumpAndSettle();
    final photo = find.byKey(const Key('meal-photo-button'));
    await tester.ensureVisible(photo);
    await tester.tap(photo);
    await tester.pumpAndSettle();
    expect(selected, ['egg']);
    expect(find.byKey(const Key('meal-photo-proposal')), findsNothing);
    expect(await db.select(db.logEntries).get(), isEmpty);
  });

  test('unknown food IDs cannot enter canonical selected-food JSON', () {
    final json = encodeMealItemIds([
      'egg', 'not_in_approved_catalog', 'egg',
    ]);
    expect(decodeMealItemIds(json), ['egg']);
  });

  test('single production draft path owns notes, voice, items, portions and one save', () {
    final code = File('lib/features/dashboard/widgets/add_log_sheet.dart')
        .readAsStringSync();
    expect(code, contains('final List<String> _selectedMealItemIds'));
    expect(code, contains('final Map<String, MealPortionSelection> _mealPortionSelections'));
    expect(code, contains('final TextEditingController _mealNoteController'));
    expect(code, contains('final current = _mealNoteController.text.trimRight();'));
    expect(code, contains('onSelectedMealItemIdsChanged: (ids)'));
    expect(code, contains('onPortionsChanged: (next)'));
    expect(code, contains('mealDescription: drift.Value(note.isEmpty ? null : note)'));
    expect(code, contains('encodeMealItemIds(_selectedMealItemIds)'));
    expect(code, contains('encodeMealPortionSelections(_mealPortionSelections.values)'));
    expect(code, contains('if (_mealVoiceBusy)'));
    final saveStart = code.indexOf('Future<void> _saveLog(');
    final clearStart = code.indexOf('void _clearDraftForNextEntry()');
    expect(saveStart, greaterThan(0));
    expect(clearStart, greaterThan(saveStart));
    final save = code.substring(saveStart, clearStart);
    expect(RegExp(r'\\.insert\\(').allMatches(save).length, 1);
  });
}
