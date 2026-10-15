// Synthetic data; real Flutter render, not a physical Android/iOS device.
import 'dart:io';
import 'dart:typed_data';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_progressive_demographics_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/features/profile/d18_profile_panel.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

const _enabled = bool.fromEnvironment('D18_CAPTURE_UI');
Future<AppDatabase> _fixture() async {
  final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734));
  await db.into(db.patientProfiles).insert(PatientProfilesCompanion.insert(
    userId: const drift.Value(734),
    preferredLanguage: const drift.Value('fr'),
    updatedAt: DateTime.utc(2026, 10, 15),
  ));
  await PatientProgressiveDemographicsStore(db).update(
    updateBirthYear: true, birthYear: 1994,
    updateGenderIdentity: true, genderIdentity: 'prefer_not_to_say',
  );
  await PatientWeightHistoryStore(db).append(
    clientUuid: 'd18c0000-1234-4abc-8def-123456789abc',
    value: '72.50', unit: 'kg',
    measuredAtUtc: DateTime.utc(2026, 10, 14, 9, 20),
  );
  return db;
}

Future<void> _capture(WidgetTester tester, String lang, Size size) async {
  final db = await _fixture();
  addTearDown(db.close);
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = size;
  final prefix = 'd18-raster-' + lang + '-' +
      size.width.toInt().toString() + 'x' + size.height.toInt().toString();
  await tester.pumpWidget(MaterialApp(
    debugShowCheckedModeBanner: false,
    locale: Locale(lang),
    supportedLocales: const [Locale('fr'), Locale('ar')],
    localizationsDelegates: const [
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    theme: ThemeData(useMaterial3: true, fontFamily: 'D18AuditDejaVu'),
    home: RepaintBoundary(
      key: const Key('d18-raster-root'),
      child: Scaffold(
        appBar: AppBar(title: Text(lang == 'ar' ? 'الملف الشخصي' : 'Profil')),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(12),
          child: D18ProfilePanel(db: db),
        ),
      ),
    ),
  ));
  await tester.pumpAndSettle();
  expect(Directionality.of(tester.element(
      find.byKey(const Key('d18-expand-profile')))),
      lang == 'ar' ? TextDirection.rtl : TextDirection.ltr);
  expect(tester.takeException(), isNull);
  await expectLater(find.byKey(const Key('d18-raster-root')),
      matchesGoldenFile('goldens/$prefix-closed.png'));

  await tester.tap(find.byKey(const Key('d18-expand-profile')));
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('d18-birth-year')), findsOneWidget);
  expect(tester.takeException(), isNull);
  await expectLater(find.byKey(const Key('d18-raster-root')),
      matchesGoldenFile('goldens/$prefix-open-top.png'));

  await tester.ensureVisible(find.byKey(const Key('d18-save-weight')));
  await tester.pumpAndSettle();
  expect(find.text('72.50 kg'), findsOneWidget);
  expect(tester.takeException(), isNull);
  await expectLater(find.byKey(const Key('d18-raster-root')),
      matchesGoldenFile('goldens/$prefix-open-bottom.png'));
  await tester.pumpWidget(const SizedBox.shrink());
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('D18 readable FR/AR raster at four viewports',
      (tester) async {
    if (!_enabled) return;
    // File I/O must escape WidgetTester's FakeAsync clock to avoid hangs.
    await tester.runAsync(() async {
      final bytes = await File(
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf').readAsBytes();
      final loader = FontLoader('D18AuditDejaVu');
      loader.addFont(Future<ByteData>.value(
          ByteData.sublistView(Uint8List.fromList(bytes))));
      await loader.load();
    });
    for (final size in <Size>[
      const Size(360, 560), const Size(390, 844),
      const Size(768, 1024), const Size(1280, 900),
    ]) {
      for (final lang in ['fr', 'ar']) {
        await _capture(tester, lang, size);
      }
    }
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}
