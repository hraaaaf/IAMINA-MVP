import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/ai_models.dart';
import 'package:amina/features/journal/widgets/meal_capture_panel.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

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
            ),
          ),
        ),
      ),
    );
  }

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
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('meal-food-search')), 'بيض');
    await tester.pump();
    final result = find.byKey(const Key('meal-search-egg'));
    expect(result, findsOneWidget);
    expect(Directionality.of(tester.element(result)), TextDirection.rtl);
    expect(find.text('Œuf'), findsNothing);
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
        harness(selected: const <String>[], onChanged: (_) {}),
      );
      await tester.pumpAndSettle();
      expect(find.text('Récents'), findsOneWidget);
      expect(find.text('Habituels'), findsOneWidget);
      expect(find.text('Œuf'), findsWidgets);
      expect(find.text('Pain marocain'), findsWidgets);
    },
  );
}
