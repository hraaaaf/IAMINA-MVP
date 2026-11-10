import 'dart:async';
import 'dart:typed_data';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/features/dashboard/widgets/add_log_view.dart';
import 'package:amina/features/journal/widgets/meal_capture_panel.dart';
import 'package:amina/services/consent_service.dart';
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
  ConsentService? consent,
}) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(
      body: MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          Provider<PatientProfileData?>.value(value: null),
          if (consent != null)
            ChangeNotifierProvider<ConsentService>.value(value: consent),
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

    testWidgets('D14 Add Log requires current verified consent for meal photo',
        (tester) async {
      _narrow(tester);
      final consent = ConsentService();
      addTearDown(consent.dispose);
      await tester.pumpWidget(_sheet(db, consent: consent));
      await tester.pumpAndSettle();
      await _tapOptionalMeal(tester);

      final panel = find.byType(MealCapturePanel);
      expect(panel, findsOneWidget);
      expect(tester.widget<MealCapturePanel>(panel).canUsePhotoRecognition,
          isFalse, reason: 'Missing evidence must fail closed');

      consent.markVerifiedConsent();
      await tester.pump();
      expect(tester.widget<MealCapturePanel>(panel).canUsePhotoRecognition,
          isTrue, reason: 'Only verified consent unlocks the local photo gate');

      consent.markWithdrawalPending();
      await tester.pump();
      expect(tester.widget<MealCapturePanel>(panel).canUsePhotoRecognition,
          isFalse, reason: 'Pending withdrawal immediately closes the photo gate');

      consent.markWithdrawalConfirmed();
      await tester.pump();
      expect(tester.widget<MealCapturePanel>(panel).canUsePhotoRecognition,
          isFalse);
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
