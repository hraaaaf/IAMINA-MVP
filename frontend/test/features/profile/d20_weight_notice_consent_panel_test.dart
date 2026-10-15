import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_notice_preferences_store.dart';
import 'package:amina/features/profile/d20_weight_notice_consent_panel.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Future<AppDatabase> _db(int id) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(id),
  );
  await db.into(db.patientProfiles).insert(PatientProfilesCompanion.insert(
    userId: drift.Value(id),
    preferredLanguage: const drift.Value('fr'),
    updatedAt: DateTime.utc(2026, 10, 15),
  ));
  return db;
}

Future<void> _render(WidgetTester tester, AppDatabase db,
    {String lang = 'fr'}) async {
  await tester.pumpWidget(MaterialApp(
    locale: Locale(lang),
    supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
    localizationsDelegates: GlobalMaterialLocalizations.delegates,
    home: Scaffold(body: SingleChildScrollView(
      child: D20WeightNoticeConsentPanel(db: db),
    )),
  ));
  await tester.pumpAndSettle();
}

Future<void> _open(WidgetTester tester) async {
  await tester.tap(find.byKey(const Key('d20-consent-expand')));
  await tester.pumpAndSettle();
}

Future<void> _fill(WidgetTester tester, {String amount = '1,50'}) async {
  for (final entry in <String, String>{
    'd20-consent-kg': amount, 'd20-consent-span': '7',
    'd20-consent-age': '14', 'd20-consent-spacing': '5',
  }.entries) {
    final field = find.byKey(Key(entry.key));
    await tester.ensureVisible(field);
    await tester.enterText(field, entry.value);
    await tester.pumpAndSettle();
  }
}

Future<void> _acceptSave(WidgetTester tester) async {
  final checkbox = find.byKey(const Key('d20-consent-choice'));
  await tester.ensureVisible(checkbox);
  await tester.tap(checkbox);
  await tester.pumpAndSettle();
  final save = find.byKey(const Key('d20-consent-save'));
  await tester.ensureVisible(save);
  await tester.tap(save);
  await tester.pumpAndSettle();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('D20-F initial OFF and collapsed: opening cannot write consent',
      (tester) async {
    final db = await _db(734);
    addTearDown(db.close);
    await _render(tester, db);
    expect(find.text('Désactivées par défaut'), findsOneWidget);
    await _open(tester);
    expect(tester.widget<FilledButton>(
      find.byKey(const Key('d20-consent-save'))).onPressed, isNull);
    expect((await PatientWeightNoticePreferencesStore(db).read()).enabled,
        false);
  });

  testWidgets('D20-F filling criteria alone cannot enable notification',
      (tester) async {
    final db = await _db(734);
    addTearDown(db.close);
    await _render(tester, db);
    await _open(tester);
    await _fill(tester);
    expect(tester.widget<FilledButton>(
      find.byKey(const Key('d20-consent-save'))).onPressed, isNull);
    expect((await PatientWeightNoticePreferencesStore(db).read()).enabled,
        false);
  });

  testWidgets('D20-F explicit agreement persists exactly chosen data',
      (tester) async {
    final db = await _db(734);
    addTearDown(db.close);
    await _render(tester, db);
    await _open(tester);
    await _fill(tester);
    await _acceptSave(tester);
    final persisted = await PatientWeightNoticePreferencesStore(db).read();
    expect(persisted.enabled, true);
    expect(persisted.minimumChangeKgHundredths, 150);
    expect(persisted.minimumSpan, const Duration(days: 7));
    expect(persisted.maximumLatestAge, const Duration(days: 14));
    expect(persisted.minimumSpacing, const Duration(days: 5));
    expect(persisted.consentedAtUtc, isNotNull);
    expect(find.textContaining('Aucun envoi dans cette version'), findsOneWidget);
    expect(tester.widget<CheckboxListTile>(
      find.byKey(const Key('d20-consent-choice'))).value, false);
  });

  testWidgets('D20-F invalid magnitude refuses persistence',
      (tester) async {
    final db = await _db(734);
    addTearDown(db.close);
    await _render(tester, db);
    await _open(tester);
    await _fill(tester, amount: '0');
    await _acceptSave(tester);
    expect((await PatientWeightNoticePreferencesStore(db).read()).enabled,
        false);
    expect(find.textContaining('Seuil positif'), findsOneWidget);
  });

  testWidgets('D20-F withdrawal erases all user criteria',
      (tester) async {
    final db = await _db(734);
    addTearDown(db.close);
    await _render(tester, db);
    await _open(tester);
    await _fill(tester);
    await _acceptSave(tester);
    final revoke = find.byKey(const Key('d20-consent-revoke'));
    await tester.ensureVisible(revoke);
    await tester.tap(revoke);
    await tester.pumpAndSettle();
    final persisted = await PatientWeightNoticePreferencesStore(db).read();
    expect(persisted.enabled, false);
    expect(persisted.minimumChangeKgHundredths, isNull);
    expect(find.textContaining('Accord retiré'), findsOneWidget);
  });

  testWidgets('D20-F vault A to B to A never carries previous opt-in',
      (tester) async {
    final a = await _db(734), b = await _db(812);
    addTearDown(a.close);
    addTearDown(b.close);
    await _render(tester, a);
    await _open(tester);
    await _fill(tester);
    await _acceptSave(tester);
    expect((await PatientWeightNoticePreferencesStore(a).read()).enabled, true);
    await _render(tester, b);
    expect(find.text('Désactivées par défaut'), findsOneWidget);
    expect((await PatientWeightNoticePreferencesStore(b).read()).enabled, false);
    await _render(tester, a);
    expect(find.textContaining('Accord enregistré'), findsOneWidget);
  });

  testWidgets('D20-F responsive FR EN AR & RTL, 390 430 768 1280',
      (tester) async {
    final db = await _db(734);
    addTearDown(db.close);
    for (final width in <double>[390, 430, 768, 1280]) {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = Size(width, 932);
      for (final language in ['fr', 'en', 'ar']) {
        await _render(tester, db, lang: language);
        final panel = find.byKey(const Key('d20-consent-panel'));
        expect(panel, findsOneWidget);
        expect(Directionality.of(tester.element(panel)),
            language == 'ar' ? TextDirection.rtl : TextDirection.ltr);
        expect(tester.takeException(), isNull);
      }
    }
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}
