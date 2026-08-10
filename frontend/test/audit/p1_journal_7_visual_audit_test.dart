import 'dart:io';
import 'dart:typed_data';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/consent_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:provider/single_child_widget.dart';

const _boundaryKey = Key('visual-audit-boundary');
const _auditFontFamily = 'AuditSans';

Future<void> _loadAuditFont() async {
  final bytes = await File(
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
  ).readAsBytes();
  final loader = FontLoader(_auditFontFamily);
  loader.addFont(Future<ByteData>.value(ByteData.sublistView(bytes)));
  await loader.load();
}

Widget _localizedHome({
  required Locale locale,
  required Widget child,
  required List<SingleChildWidget> providers,
}) {
  return MaterialApp(
    locale: locale,
    theme: ThemeData(fontFamily: _auditFontFamily),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: MultiProvider(
      providers: providers,
      child: RepaintBoundary(key: _boundaryKey, child: child),
    ),
  );
}

Future<void> _setSize(WidgetTester tester, Size size, AppDatabase db) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(() async {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
    await db.close();
  });
}

Future<PatientProfileData> _configuredProfile(
  AppDatabase db, {
  required DateTime start,
  required DateTime end,
}) async {
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: const drift.Value(1),
      updatedAt: DateTime(2026, 8, 10, 8),
      diabetesType: const drift.Value('type2'),
      treatment: const drift.Value('lifestyle'),
      ramadanStartDate: drift.Value(start),
      ramadanEndDate: drift.Value(end),
    ),
  );
  return db.select(db.patientProfiles).getSingle();
}

Future<void> _openRamadanProfileSection(WidgetTester tester) async {
  final section = find.byKey(const ValueKey('profile-ramadan-section'));
  expect(section, findsOneWidget);
  await tester.ensureVisible(section);
  await tester.pumpAndSettle();
  final tile = find.descendant(of: section, matching: find.byType(ExpansionTile));
  expect(tile, findsOneWidget);
  await tester.tap(tile);
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('ramadan-start-date')), findsOneWidget);
  expect(find.byKey(const Key('ramadan-end-date')), findsOneWidget);
  expect(find.byKey(const Key('ramadan-save-period')), findsOneWidget);
}

Future<void> _openMealSection(WidgetTester tester) async {
  final mealButton = find.byKey(const Key('add-meal-button'));
  expect(mealButton, findsOneWidget);
  await tester.ensureVisible(mealButton);
  await tester.pumpAndSettle();

  // AddLogSheet has a fixed save bar. Move the meal CTA above that overlay
  // before tapping so this remains a real hit-tested interaction.
  final scrollable = find.byType(Scrollable).first;
  await tester.drag(scrollable, const Offset(0, -180));
  await tester.pumpAndSettle();
  await tester.tap(mealButton);
  await tester.pumpAndSettle();
}

void main() {
  setUpAll(_loadAuditFont);

  final cases = <(String, Locale, Size)>[
    ('fr-desktop-1440x1000', const Locale('fr'), const Size(1440, 1000)),
    ('fr-tablet-768x1024', const Locale('fr'), const Size(768, 1024)),
    ('fr-mobile-390x844', const Locale('fr'), const Size(390, 844)),
    ('fr-small-360x560', const Locale('fr'), const Size(360, 560)),
    ('ar-desktop-1440x1000', const Locale('ar'), const Size(1440, 1000)),
    ('ar-tablet-768x1024', const Locale('ar'), const Size(768, 1024)),
    ('ar-mobile-390x844', const Locale('ar'), const Size(390, 844)),
    ('ar-small-360x560', const Locale('ar'), const Size(360, 560)),
  ];

  for (final item in cases) {
    testWidgets('profile Ramadan expanded top ${item.$1}', (tester) async {
      final db = AppDatabase(NativeDatabase.memory());
      await _setSize(tester, item.$3, db);
      final profile = await _configuredProfile(
        db,
        start: DateTime(2026, 2, 18),
        end: DateTime(2026, 3, 20),
      );
      final consent = ConsentService()..seedInitialProfile(profile);
      addTearDown(consent.dispose);

      await tester.pumpWidget(
        _localizedHome(
          locale: item.$2,
          providers: [
            Provider<AppDatabase>.value(value: db),
            ChangeNotifierProvider<ConsentService>.value(value: consent),
          ],
          child: const ProfileScreen(),
        ),
      );
      await tester.pumpAndSettle();
      await _openRamadanProfileSection(tester);
      expect(tester.takeException(), isNull);

      await expectLater(
        find.byKey(_boundaryKey),
        matchesGoldenFile('goldens/p1j7-profile-top-${item.$1}.png'),
      );
    });

    testWidgets('profile Ramadan controls reachable ${item.$1}', (tester) async {
      final db = AppDatabase(NativeDatabase.memory());
      await _setSize(tester, item.$3, db);
      final profile = await _configuredProfile(
        db,
        start: DateTime(2026, 2, 18),
        end: DateTime(2026, 3, 20),
      );
      final consent = ConsentService()..seedInitialProfile(profile);
      addTearDown(consent.dispose);

      await tester.pumpWidget(
        _localizedHome(
          locale: item.$2,
          providers: [
            Provider<AppDatabase>.value(value: db),
            ChangeNotifierProvider<ConsentService>.value(value: consent),
          ],
          child: const ProfileScreen(),
        ),
      );
      await tester.pumpAndSettle();
      await _openRamadanProfileSection(tester);
      await tester.ensureVisible(find.byKey(const Key('ramadan-save-period')));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);

      await expectLater(
        find.byKey(_boundaryKey),
        matchesGoldenFile('goldens/p1j7-profile-controls-${item.$1}.png'),
      );
    });

    testWidgets('active-period Add Log vocabulary ${item.$1}', (tester) async {
      final db = AppDatabase(NativeDatabase.memory());
      await _setSize(tester, item.$3, db);
      final now = DateTime.now();
      final profile = await _configuredProfile(
        db,
        start: now.subtract(const Duration(days: 1)),
        end: now.add(const Duration(days: 1)),
      );

      await tester.pumpWidget(
        _localizedHome(
          locale: item.$2,
          providers: [
            Provider<AppDatabase>.value(value: db),
            Provider<PatientProfileData?>.value(value: profile),
          ],
          child: const AddLogSheet(isPage: true),
        ),
      );
      await tester.pumpAndSettle();
      await _openMealSection(tester);

      expect(find.byKey(const Key('ramadan-meal-vocabulary-hint')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-suhoor')), findsOneWidget);
      expect(find.byKey(const Key('meal-type-iftar')), findsOneWidget);
      for (final key in <String>['suhoor', 'iftar', 'snack', 'other']) {
        expect(
          tester.widget<ChoiceChip>(find.byKey(Key('meal-type-$key'))).selected,
          isFalse,
        );
      }
      expect(tester.takeException(), isNull);

      await expectLater(
        find.byKey(_boundaryKey),
        matchesGoldenFile('goldens/p1j7-add-${item.$1}.png'),
      );
    });
  }
}
