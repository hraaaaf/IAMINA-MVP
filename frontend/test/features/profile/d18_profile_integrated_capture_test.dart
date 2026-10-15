// Captures the current IAMINA ProfileScreen, never a replacement Scaffold.
import 'dart:io';
import 'dart:typed_data';
import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/core/widgets/mobile_page_header.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_progressive_demographics_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/sync_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

const enabled = bool.fromEnvironment('D18_CAPTURE_UI');
const captureConsent = bool.fromEnvironment('D20_CAPTURE_CONSENT');
class _UnlockedFixture extends AppLockService {
  @override
  bool get isUnlocked => true;
}

Future<void> _loadFonts(WidgetTester tester) async {
  await tester.runAsync(() async {
    Future<void> load(String family, String path) async {
      final bytes = await File(path).readAsBytes();
      final loader = FontLoader(family);
      loader.addFont(Future<ByteData>.value(
        ByteData.sublistView(Uint8List.fromList(bytes))));
      await loader.load();
    }
    const fallback = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';
    await load('Inter', fallback);
    await load('Inter Tight', fallback);
    // Material buttons may request Roboto even when app body uses Inter.
    // WidgetTester's default Ahem font would draw block placeholders.
    await load('Roboto', fallback);
    // The Flutter test harness uses Ahem for some inherited Material labels.
    // Override that audit-only family with readable, Arabic-capable glyphs.
    await load('Ahem', fallback);
    // The current IAMINA header explicitly uses the bundled Georgia family.
    // Load the real product asset so French headings are not Ahem blocks.
    await load('Georgia', 'assets/fonts/IAMINASerif-Bold-subset.ttf');
    final root = Platform.environment['FLUTTER_ROOT'];
    if (root == null || root.isEmpty) throw StateError('FLUTTER_ROOT missing');
    await load('MaterialIcons',
        '$root/bin/cache/artifacts/material_fonts/MaterialIcons-Regular.otf');
  });
}

Future<void> _capture(WidgetTester tester, String lang, Size size) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(734));
  final auth = AuthService();
  final lock = _UnlockedFixture();
  final api = ApiClient(authService: auth);
  final consent = ConsentService();
  final sync = SyncService(db, api);
  addTearDown(() async {
    await db.close(); auth.dispose(); lock.dispose(); consent.dispose();
  });
  await db.into(db.patientProfiles).insert(PatientProfilesCompanion.insert(
    userId: const drift.Value(734),
    preferredLanguage: const drift.Value('fr'),
    updatedAt: DateTime.utc(2026, 10, 15),
  ));
  await PatientProgressiveDemographicsStore(db).update(
    updateBirthYear: true, birthYear: 1994,
    updateGenderIdentity: true, genderIdentity: 'prefer_not_to_say');
  await PatientWeightHistoryStore(db).append(
    clientUuid: 'd18b0000-1234-4abc-8def-123456789abc',
    value: '70.00', unit: 'kg',
    measuredAtUtc: DateTime.utc(2026, 10, 11, 9, 20));
  await PatientWeightHistoryStore(db).append(
    clientUuid: 'd18c0000-1234-4abc-8def-123456789abc',
    value: '72.50', unit: 'kg',
    measuredAtUtc: DateTime.utc(2026, 10, 14, 9, 20));
  final profile = await db.getProfileForLocalUserId(db.activeProfileRowId);
  consent.seedInitialProfile(profile);
  consent.attachStream(db.watchProfile());

  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  final prefix = 'd18-real-profile-' + lang + '-' +
      size.width.toInt().toString() + 'x' + size.height.toInt().toString();
  await tester.pumpWidget(MultiProvider(
    providers: [
      Provider<AppDatabase>.value(value: db),
      ChangeNotifierProvider<AppLockService>.value(value: lock),
      ChangeNotifierProvider<AuthService>.value(value: auth),
      Provider<ApiClient>.value(value: api),
      Provider<SyncService>.value(value: sync),
      ChangeNotifierProvider<ConsentService>.value(value: consent),
      ChangeNotifierProvider<TweaksNotifier>(create: (_) => TweaksNotifier()),
      StreamProvider<PatientProfileData?>(
        create: (_) => db.watchProfile(), initialData: profile),
    ],
    child: MaterialApp(
      debugShowCheckedModeBanner: false,
      locale: Locale(lang),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: AminaVisualLanguage.harmonize(AminaTheme.light),
      darkTheme: AminaVisualLanguage.harmonize(AminaTheme.dark),
      home: const RepaintBoundary(
        key: Key('d18-canonical-profile'), child: ProfileScreen()),
    ),
  ));
  await tester.pumpAndSettle();
  expect(find.byType(ProfileScreen), findsOneWidget);
  if (size.width < 700) {
    final header = find.byType(AminaMobilePageHeader);
    expect(header, findsOneWidget);
    final title = tester.widget<Text>(find.descendant(
      of: header, matching: find.byType(Text)).first);
    // Arabic title must not force the bundled Latin-only Georgia subset.
    expect(title.style?.fontFamily, lang == 'ar' ? isNot('Georgia') : 'Georgia');
    expect(title.style?.fontFamilyFallback, contains('Inter'));
  }
  expect(find.byKey(const Key('d18-expand-profile')), findsOneWidget);
  expect(tester.takeException(), isNull);
  await expectLater(find.byKey(const Key('d18-canonical-profile')),
      matchesGoldenFile('goldens/$prefix-top.png'));

  await tester.ensureVisible(find.byKey(const Key('d18-expand-profile')));
  await tester.pumpAndSettle();
  await tester.tap(find.byKey(const Key('d18-expand-profile')));
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('d18-birth-year')), findsOneWidget);
  expect(tester.takeException(), isNull);
  await expectLater(find.byKey(const Key('d18-canonical-profile')),
      matchesGoldenFile('goldens/$prefix-open.png'));

  await tester.ensureVisible(find.byKey(const Key('d18-save-weight')));
  await tester.pumpAndSettle();
  expect(find.text('72.50 kg'), findsOneWidget);
  expect(tester.takeException(), isNull);
  await expectLater(find.byKey(const Key('d18-canonical-profile')),
      matchesGoldenFile('goldens/$prefix-history.png'));
  await tester.ensureVisible(find.byKey(const Key('d20-weight-trend-card')));
  await tester.pumpAndSettle();
  expect(tester.takeException(), isNull);
  await expectLater(find.byKey(const Key('d18-canonical-profile')),
      matchesGoldenFile('goldens/d20-trend-' + lang + '-' +
          size.width.toInt().toString() + 'x' +
          size.height.toInt().toString() + '.png'));
  if (captureConsent) {
    expect(find.byKey(const Key('d20-consent-panel')), findsOneWidget);
    await tester.ensureVisible(find.byKey(const Key('d20-consent-panel')));
    await tester.pumpAndSettle();
    await expectLater(find.byKey(const Key('d18-canonical-profile')),
      matchesGoldenFile('goldens/d20-consent-' + lang + '-' +
          size.width.toInt().toString() + 'x' +
          size.height.toInt().toString() + '-closed.png'));
    await tester.tap(find.byKey(const Key('d20-consent-expand')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('d20-consent-save')));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await expectLater(find.byKey(const Key('d18-canonical-profile')),
      matchesGoldenFile('goldens/d20-consent-' + lang + '-' +
          size.width.toInt().toString() + 'x' +
          size.height.toInt().toString() + '-open.png'));
  }
  await tester.pumpWidget(const SizedBox.shrink());
  await tester.pump();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('D18 integrated IAMINA ProfileScreen FR/AR RTL',
      (tester) async {
    if (!enabled) return;
    await _loadFonts(tester);
    for (final size in <Size>[
      const Size(390, 844), const Size(430, 932),
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
