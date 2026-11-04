import 'dart:async';
import 'dart:typed_data';

import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/core/data/nutrition_catalog.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/ai_models.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/features/dashboard/widgets/add_log_view.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:record/record.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

Widget _sheet(
  AppDatabase db, {
  Locale locale = const Locale('fr'),
  AddLogSheet sheet = const AddLogSheet(),
  PatientProfileData? profile,
}) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(
      body: MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          Provider<PatientProfileData?>.value(value: profile),
        ],
        child: sheet,
      ),
    ),
  );
}

void _narrow(WidgetTester tester) {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
}

void _wide(WidgetTester tester) {
  tester.view.physicalSize = const Size(1440, 1000);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
}

/// The D22 dial increases entry height: below-fold chips and the meal
/// action must be scrolled CLEAR of the persistent save bar before tapping.
Future<void> _tapFormItem(WidgetTester tester, Finder target) async {
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  await tester.drag(
    find.byType(SingleChildScrollView).first,
    const Offset(0, -175),
  );
  await tester.pumpAndSettle();
  await tester.tap(target);
  await tester.pumpAndSettle();
}

Future<void> _tapCatalogResult(WidgetTester tester, Finder target) async {
  // Keep the result in the visible center; the generic -175 drag can
  // move a search result above the viewport on 390px screens.
  tester.binding.focusManager.primaryFocus?.unfocus();
  await tester.pumpAndSettle();
  // Widget tests run in fake async: awaiting an animated Scrollable.ensureVisible
  // before pumping deadlocks the test. WidgetTester drives the scroll safely.
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  await tester.tap(target);
  await tester.pumpAndSettle();
}

Future<void> _tapOptionalMeal(WidgetTester tester) =>
    _tapFormItem(tester, find.byKey(const Key('add-meal-button')));

void main() {
  late AppDatabase db;

  setUp(() => db = _openDb());
  tearDown(() async => db.close());

  group('Add Log focused glucose journal', () {
    test('keeps hypoglycemia safety boundaries deterministic', () {
      expect(classifyGlucoseEntrySafety(53), GlucoseEntrySafety.level2Low);
      expect(classifyGlucoseEntrySafety(54), GlucoseEntrySafety.level1Low);
      expect(classifyGlucoseEntrySafety(69), GlucoseEntrySafety.level1Low);
      expect(classifyGlucoseEntrySafety(70), GlucoseEntrySafety.nonLow);
      expect(classifyGlucoseEntrySafety(112), GlucoseEntrySafety.nonLow);
    });

    testWidgets('112 mg/dL is saved without a low-glucose warning', (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '112');
      await tester.pumpAndSettle();
      final input = tester.widget<TextField>(
        find.byKey(const Key('glucose-input')),
      );
      expect(input.controller?.text, '112');

      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('level2-low-dialog')), findsNothing);
      expect(find.byKey(const Key('level1-low-dialog')), findsNothing);
      final logs = await db.select(db.logEntries).get();
      expect(logs, hasLength(1));
      expect(logs.single.bloodSugar, 112);
      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
    });

    test('uses Opus/WebM on web and AAC/MP4 on mobile', () {
      expect(
        mealVoiceRecordConfig(isWeb: true).encoder,
        AudioEncoder.opus,
      );
      expect(
        mealVoiceRecordConfig(isWeb: false).encoder,
        AudioEncoder.aacLc,
      );
      expect(mealVoiceMimeType(isWeb: true), 'audio/webm');
      expect(mealVoiceMimeType(isWeb: false), 'audio/mp4');
    });

    testWidgets('starts blank with save disabled and no inferred context', (
      tester,
    ) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      final glucose = tester.widget<TextField>(
        find.byKey(const Key('glucose-input')),
      );
      expect(glucose.controller?.text, isEmpty);
      expect(
        find.text('Aucune valeur n’est supposée avant ta saisie.'),
        findsOneWidget,
      );
      expect(
        tester
            .widget<ChoiceChip>(
              find.byKey(const Key('glycemic-context-fasting')),
            )
            .selected,
        isFalse,
      );
      expect(
        tester.widget<FilledButton>(find.byKey(const Key('save-log-button'))).onPressed,
        isNull,
      );
    });

    testWidgets('enables save only after a valid glucose value', (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.pump();

      expect(
        tester.widget<FilledButton>(find.byKey(const Key('save-log-button'))).onPressed,
        isNotNull,
      );
    });

    testWidgets('keeps meal and measurement context separate and optional', (
      tester,
    ) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.text('CONTEXTE DE LA MESURE'), findsOneWidget);
      expect(find.byKey(const Key('add-meal-button')), findsOneWidget);
      expect(find.byKey(const Key('meal-section')), findsNothing);

      await _tapOptionalMeal(tester);

      expect(find.byKey(const Key('meal-section')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-breakfast')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-lunch')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-dinner')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-snack')), findsOneWidget);
    });

    testWidgets(
      'voice dictation stays draft-only, locks actions, then remains editable',
      (tester) async {
        _narrow(tester);
        final audioBytes = Uint8List.fromList(<int>[1, 2, 3, 4]);
        final transcriberStarted = Completer<void>();
        final transcript = Completer<String?>();
        RecordConfig? startConfig;
        Uint8List? transcribedBytes;
        String? transcribedMime;

        final sheet = AddLogSheet(
          voicePermissionCheck: () async => true,
          voiceStartStream: (config) async {
            startConfig = config;
            return const Stream<Uint8List>.empty();
          },
          voiceStopAndRead: () async => audioBytes,
          voiceTranscriber: (bytes, mimeType) {
            transcribedBytes = bytes;
            transcribedMime = mimeType;
            if (!transcriberStarted.isCompleted) transcriberStarted.complete();
            return transcript.future;
          },
        );

        await tester.pumpWidget(_sheet(db, sheet: sheet));
        await tester.pumpAndSettle();
        await tester.enterText(find.byKey(const Key('glucose-input')), '126');
        await _tapOptionalMeal(tester);

        final voiceButton = find.byKey(
          const Key('meal-note-voice-button'),
        );
        await tester.ensureVisible(voiceButton);
        await tester.pumpAndSettle();
        final capture = tester.widget<AddLogMealCapture>(
          find.byType(AddLogMealCapture),
        );
        await capture.onVoiceToggle();
        await tester.pumpAndSettle();
        expect(startConfig?.encoder, AudioEncoder.aacLc);
        expect(
          tester
              .widget<FilledButton>(
                find.byKey(const Key('save-log-button')),
              )
              .onPressed,
          isNull,
        );
        expect(
          tester
              .widget<TextButton>(
                find.byKey(const Key('remove-meal-button')),
              )
              .onPressed,
          isNull,
        );

        final stopFuture = tester
            .widget<AddLogMealCapture>(find.byType(AddLogMealCapture))
            .onVoiceToggle();
        await transcriberStarted.future;

        expect(transcribedBytes, isNotNull);
        expect(transcribedBytes, hasLength(4));
        expect(transcribedMime, 'audio/mp4');
        expect(
          tester
              .widget<FilledButton>(
                find.byKey(const Key('save-log-button')),
              )
              .onPressed,
          isNull,
        );
        expect(await db.select(db.logEntries).get(), isEmpty);

        transcript.complete('Salade et pain');
        await stopFuture;
        await tester.pumpAndSettle();

        final note = tester.widget<TextField>(
          find.byKey(const Key('meal-note-input')),
        );
        expect(note.controller?.text, 'Salade et pain');
        expect(note.readOnly, isFalse);
        expect(
          tester
              .widget<FilledButton>(
                find.byKey(const Key('save-log-button')),
              )
              .onPressed,
          isNotNull,
        );
        expect(await db.select(db.logEntries).get(), isEmpty);

        await tester.enterText(
          find.byKey(const Key('meal-note-input')),
          'Salade et pain + yaourt',
        );
        await tester.tap(find.byKey(const Key('save-log-button')));
        await tester.pumpAndSettle();

        final logs = await db.select(db.logEntries).get();
        expect(logs, hasLength(1));
        expect(logs.single.mealDescription, 'Salade et pain + yaourt');
      },
    );

    testWidgets('mobile exposes time and additional context in one step', (
      tester,
    ) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('journal-details-button')), findsNothing);
      expect(find.byKey(const Key('journal-details-card')), findsOneWidget);
      expect(find.byKey(const Key('journal-context-button')), findsNothing);
      expect(find.byKey(const Key('context-stress')), findsOneWidget);
      expect(find.byKey(const Key('insulin-taken-input')), findsNothing);
      expect(
        find.textContaining('Date et heure préremplies automatiquement'),
        findsOneWidget,
      );
    });

    testWidgets('desktop keeps primary event and optional context side by side', (
      tester,
    ) async {
      _wide(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('journal-details-button')), findsNothing);
      expect(find.byKey(const Key('journal-details-card')), findsOneWidget);
      expect(find.byKey(const Key('glucose-input')), findsOneWidget);
      expect(find.byKey(const Key('add-meal-button')), findsOneWidget);
      expect(find.byKey(const Key('insulin-taken-input')), findsNothing);
    });

    testWidgets('persists glucose context and meal with insulin always null', (
      tester,
    ) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await _tapFormItem(tester,
        find.byKey(const Key('glycemic-context-pre_meal')),
      );
      await _tapOptionalMeal(tester);
      await tester.tap(find.byKey(const Key('meal-type-lunch')));
      await tester.enterText(
        find.byKey(const Key('meal-note-input')),
        'Salade et pain',
      );
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      final logs = await db.select(db.logEntries).get();
      expect(logs, hasLength(1));
      expect(logs.single.bloodSugar, 126);
      expect(logs.single.glycemicContext, 'pre_meal');
      expect(logs.single.mealType, 'lunch');
      expect(logs.single.mealDescription, 'Salade et pain');
      expect(logs.single.insulinUnits, isNull);
    });

    testWidgets('additional context remains factual and optional', (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.pump();
      final stressChip = find.byKey(const Key('context-stress'));
      await tester.ensureVisible(stressChip);
      await tester.pumpAndSettle();
      await tester.tap(stressChip);
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      final logs = await db.select(db.logEntries).get();
      expect(logs.single.isStressed, isTrue);
      expect(logs.single.insulinUnits, isNull);
    });

    testWidgets('Arabic remains real localized RTL content', (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db, locale: const Locale('ar')));
      await tester.pumpAndSettle();

      expect(find.text('قياس جديد'), findsOneWidget);
      expect(find.text('سياق القياس'), findsOneWidget);
      expect(find.text('إضافة وجبة · اختياري'), findsOneWidget);
      expect(find.text('Nouvelle mesure'), findsNothing);
      await _tapOptionalMeal(tester);
      expect(find.byTooltip('إملاء ملاحظة الوجبة'), findsOneWidget);
      expect(
        Directionality.of(tester.element(find.text('قياس جديد'))),
        TextDirection.rtl,
      );
    });

    testWidgets('does not expose fabricated nutrition or treatment judgement', (
      tester,
    ) async {
      _wide(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      expect(find.textContaining('IG 35'), findsNothing);
      expect(find.textContaining('Dose standard'), findsNothing);
      expect(find.textContaining('Dose critique'), findsNothing);
      expect(find.textContaining('Analyse IAmina'), findsNothing);
      expect(find.byKey(const Key('insulin-taken-input')), findsNothing);
    });
  });

  group('D15 real AddLogSheet Save — one local meal draft', () {
    for (final locale in const <Locale>[Locale('fr'), Locale('ar')]) {
      for (final viewport in const <String>['390x844', '1440x1000']) {
        testWidgets(
          'manual catalog + measured grams + multilingual note save exactly once '
          '${locale.languageCode} ${viewport}',
          (tester) async {
            // Stage markers make a hung widget interaction diagnosable in CI.
            void stage(String name) =>
                print('D15_STAGE=${locale.languageCode}:$viewport:$name');
            stage('start');
            if (viewport == '390x844') {
              _narrow(tester);
            } else {
              _wide(tester);
            }
            await tester.pumpWidget(_sheet(db, locale: locale));
            await tester.pumpAndSettle();

            await tester.enterText(
              find.byKey(const Key('glucose-input')), '126');
            stage('glucose_entered');
            await _tapOptionalMeal(tester);
            stage('meal_opened');
            await tester.enterText(
              find.byKey(const Key('meal-food-search')),
              locale.languageCode == 'ar' ? 'بيض' : 'oeuf',
            );
            await tester.pumpAndSettle();

            stage('search_entered');
            final egg = find.byKey(const Key('meal-search-egg'));
            expect(egg, findsOneWidget);
            stage('egg_visible');
            await _tapCatalogResult(tester, egg);
            stage('egg_selected');
            expect(find.byKey(const Key('meal-selected-egg')), findsOneWidget);

            final grams = find.byKey(const Key('nutrition-grams-egg'));
            expect(grams, findsOneWidget);
            await tester.ensureVisible(grams);
            await tester.enterText(grams, '75');
            stage('grams_entered');
            const noteText = 'Œuf / بيض — 75 g déclarés, test synthétique';
            final note = find.byKey(const Key('meal-note-input'));
            await tester.ensureVisible(note);
            await tester.enterText(note, noteText);
            stage('note_entered');
            await tester.pumpAndSettle();

            // Changing any draft field must not insert an event.
            expect(await db.select(db.logEntries).get(), isEmpty);
            stage('before_save');
            await tester.tap(find.byKey(const Key('save-log-button')));
            stage('save_tapped');
            await tester.pumpAndSettle();

            final rows = await db.select(db.logEntries).get();
            expect(rows, hasLength(1), reason: 'One explicit Save = one Drift row');
            final saved = rows.single;
            expect(saved.bloodSugar, 126);
            expect(saved.mealDescription, noteText);
            expect(decodeMealItemIds(saved.mealItemsJson), <String>['egg']);
            final portions = decodeMealPortionSelections(saved.mealPortionsJson);
            expect(portions, hasLength(1));
            expect(portions.single.foodId, 'egg');
            expect(portions.single.grams, 75.0);
            expect(saved.insulinUnits, isNull);
            expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
            stage('done');
          },
          timeout: const Timeout(Duration(seconds: 40)),
        );
      }
    }

    testWidgets('discard meal draft clears items, note and grams before Save',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('glucose-input')), '126');
      await _tapOptionalMeal(tester);
      await tester.enterText(
        find.byKey(const Key('meal-food-search')), 'oeuf');
      await tester.pumpAndSettle();
      await _tapCatalogResult(
        tester, find.byKey(const Key('meal-search-egg')));
      final grams = find.byKey(const Key('nutrition-grams-egg'));
      await tester.ensureVisible(grams);
      await tester.enterText(grams, '75');
      final note = find.byKey(const Key('meal-note-input'));
      await tester.ensureVisible(note);
      await tester.enterText(note, 'Brouillon à abandonner');
      expect(await db.select(db.logEntries).get(), isEmpty);

      // The generic helper drags another 175px after ensureVisible, moving
      // this top-of-section Remove action outside the hit-test viewport.
      final removeMeal = find.byKey(const Key('remove-meal-button'));
      tester.binding.focusManager.primaryFocus?.unfocus();
      await tester.pumpAndSettle();
      await tester.ensureVisible(removeMeal);
      await tester.pumpAndSettle();
      await tester.tap(removeMeal);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('meal-section')), findsNothing);
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      final rows = await db.select(db.logEntries).get();
      expect(rows, hasLength(1));
      expect(rows.single.mealDescription, isNull);
      expect(decodeMealItemIds(rows.single.mealItemsJson), isEmpty);
      expect(decodeMealPortionSelections(rows.single.mealPortionsJson), isEmpty);
      expect(rows.single.insulinUnits, isNull);
    });
  });

  group('D15 photo confirmation through real Save (synthetic only)', () {
    testWidgets('confirmed photo candidate remains local until one explicit Save', (tester) async {
      _wide(tester);
      final profile = PatientProfileData(
        userId: 1,
        preferredLanguage: 'fr',
        updatedAt: DateTime.utc(2026, 11, 4),
        targetRangeLow: 70,
        targetRangeHigh: 180,
        unitPreference: 'mg/dL',
        aiConsentGivenAt: DateTime.utc(2026, 11, 4),
      );
      await tester.pumpWidget(_sheet(
        db,
        profile: profile,
        sheet: AddLogSheet(
          photoRecognition: () async => const MealAnalysisResult(
            foods: ['pain complet'],
            confidence: 'high',
            fallback: false,
          ),
        ),
      ));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await _tapOptionalMeal(tester);
      final photo = find.byKey(const Key('meal-photo-button'));
      await tester.ensureVisible(photo);
      await tester.tap(photo);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('meal-photo-proposal')), findsOneWidget);
      expect(await db.select(db.logEntries).get(), isEmpty);

      final candidate = find.byKey(
        const Key('meal-photo-candidate-whole_grain_bread'),
      );
      await tester.ensureVisible(candidate);
      await tester.tap(candidate);
      await tester.pumpAndSettle();
      expect(await db.select(db.logEntries).get(), isEmpty);

      final confirm = find.byKey(const Key('meal-photo-confirm'));
      await tester.ensureVisible(confirm);
      await tester.tap(confirm);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('meal-selected-whole_grain_bread')), findsOneWidget);
      expect(await db.select(db.logEntries).get(), isEmpty);

      final grams = find.byKey(const Key('nutrition-grams-whole_grain_bread'));
      await tester.ensureVisible(grams);
      await tester.enterText(grams, '75');
      await tester.enterText(
        find.byKey(const Key('meal-note-input')),
        'Pain confirmé / خبز — test synthétique',
      );
      expect(await db.select(db.logEntries).get(), isEmpty);
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      final rows = await db.select(db.logEntries).get();
      expect(rows, hasLength(1));
      expect(rows.single.bloodSugar, 126);
      expect(rows.single.mealDescription, 'Pain confirmé / خبز — test synthétique');
      expect(decodeMealItemIds(rows.single.mealItemsJson), ['whole_grain_bread']);
      final portions = decodeMealPortionSelections(rows.single.mealPortionsJson);
      expect(portions, hasLength(1));
      expect(portions.single.foodId, 'whole_grain_bread');
      expect(portions.single.grams, 75.0);
      expect(rows.single.insulinUnits, isNull);
      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
    });
  });

  group('Add Log post-save receipt', () {
    testWidgets('successful save shows factual receipt and resets next draft', (
      tester,
    ) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await _tapFormItem(tester,
        find.byKey(const Key('glycemic-context-post_meal')),
      );
      await _tapOptionalMeal(tester);
      await tester.tap(find.byKey(const Key('meal-type-lunch')));
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      final logs = await db.select(db.logEntries).get();
      expect(logs, hasLength(1));
      expect(logs.single.insulinUnits, isNull);

      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
      expect(find.text('Enregistrée sur cet appareil.'), findsOneWidget);
      expect(find.textContaining('126 mg/dL'), findsOneWidget);
      expect(find.textContaining('Après repas'), findsOneWidget);
      expect(find.textContaining('Déjeuner'), findsOneWidget);
      expect(find.textContaining(' U'), findsNothing);
      expect(
        find.textContaining('n’interprète pas la mesure'),
        findsNothing,
      );
      final d17Info = find.byKey(const Key('d17-receipt-info'));
      await tester.ensureVisible(d17Info);
      await tester.tap(d17Info);
      await tester.pumpAndSettle();
      expect(
        find.textContaining('n’interprète pas la mesure'),
        findsOneWidget,
      );

      final addAnother = find.byKey(const Key('post-save-add-another'));
      await tester.ensureVisible(addAnother);
      await tester.pumpAndSettle();
      await tester.tap(addAnother);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('post-save-receipt')), findsNothing);
      final glucose = tester.widget<TextField>(
        find.byKey(const Key('glucose-input')),
      );
      expect(glucose.controller?.text, isEmpty);
      expect(find.byKey(const Key('meal-section')), findsNothing);
      expect(find.byKey(const Key('journal-details-card')), findsOneWidget);
    });

    testWidgets('Arabic receipt is localized RTL and factual', (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db, locale: const Locale('ar')));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.pump();
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
      expect(find.text('تم الحفظ على هذا الجهاز.'), findsOneWidget);
      expect(find.text('عرض في السجل'), findsOneWidget);
      expect(find.text('إضافة قياس آخر'), findsOneWidget);
      expect(
        Directionality.of(
          tester.element(find.text('تم الحفظ على هذا الجهاز.')),
        ),
        TextDirection.rtl,
      );
      expect(tester.takeException(), isNull);
    });
  });
}
