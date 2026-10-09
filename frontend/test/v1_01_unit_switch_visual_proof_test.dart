import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/edit_log_screen.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart' show FontLoader;
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

/// Exact same real Flutter widget state at baseline versus candidate HEAD.
/// Used only by the CI visual-proof job, never included in production builds.
void main() {
  const phase = String.fromEnvironment(
    'V1_01_UNIT_PHASE',
    defaultValue: 'after',
  );
  assert(phase == 'before' || phase == 'after');

  setUpAll(() async {
    // Widget tests default to the Ahem placeholder. Load an actual open
    // system font so the BEFORE/AFTER text and units can be inspected.
    final file = File('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');
    if (!file.existsSync()) {
      throw StateError('Missing CI proof font: DejaVu Sans');
    }
    final fontBytes = ByteData.sublistView(file.readAsBytesSync());
    final loader = FontLoader('Roboto')
      ..addFont(Future<ByteData>.value(fontBytes));
    await loader.load();
  });

  for (final size in <Size>[const Size(390, 844), const Size(768, 1024)]) {
    testWidgets('unit-switch visual proof ${size.width.toInt()}px, $phase',
        (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      final timestamp = DateTime(2026, 9, 20, 10, 30);
      await db.into(db.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const Value(1),
          updatedAt: timestamp,
          unitPreference: const Value('mmol/L'),
        ),
      );
      final id = await db.into(db.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: timestamp,
          bloodSugar: 69.9,
          loggedAt: Value(timestamp),
          clientUuid: 'v101-unit-proof-${size.width.toInt()}',
        ),
      );
      final initialProfile = await db.select(db.patientProfiles).getSingle();
      final profileNotifier =
          ValueNotifier<PatientProfileData?>(initialProfile);
      addTearDown(profileNotifier.dispose);
      final router = GoRouter(
        initialLocation: '/journal/$id/edit',
        routes: [
          GoRoute(
            path: '/journal/:id/edit',
            builder: (_, state) => EditLogScreen(
              logId: int.parse(state.pathParameters['id']!),
            ),
          ),
          GoRoute(
            path: '/journal',
            builder: (_, __) =>
                const Scaffold(body: Text('Journal returned')),
          ),
        ],
      );
      addTearDown(router.dispose);
      const captureKey = Key('v101-edit-unit-proof-canvas');
      await tester.pumpWidget(
        RepaintBoundary(
          key: captureKey,
          child: ValueListenableBuilder<PatientProfileData?>(
            valueListenable: profileNotifier,
            builder: (_, profile, __) => MultiProvider(
              providers: [
                Provider<AppDatabase>.value(value: db),
                Provider<PatientProfileData?>.value(value: profile),
                ChangeNotifierProvider<TweaksNotifier>(
                  create: (_) => TweaksNotifier(),
                ),
              ],
              child: MaterialApp.router(
                theme: ThemeData(fontFamily: 'Roboto'),
                locale: const Locale('fr'),
                localizationsDelegates:
                    AppLocalizations.localizationsDelegates,
                supportedLocales: AppLocalizations.supportedLocales,
                routerConfig: router,
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final field = find.byKey(const Key('edit-glucose-input'));
      expect(field, findsOneWidget);
      expect(tester.widget<TextField>(field).controller!.text, '3.9');
      expect(
        tester.widget<TextField>(field).decoration!.suffixText,
        'mmol/L',
      );

      // Same user action and same patient fixture in BEFORE and AFTER.
      profileNotifier.value =
          initialProfile.copyWith(unitPreference: 'mg/dL');
      await tester.pumpAndSettle();

      final expectedUnit = phase == 'before' ? 'mg/dL' : 'mmol/L';
      expect(tester.widget<TextField>(field).controller!.text, '3.9');
      expect(
        tester.widget<TextField>(field).decoration!.suffixText,
        expectedUnit,
      );
      expect(tester.takeException(), isNull);

      final proofDir = Platform.environment['IAMINA_V101_PROOF_DIR'];
      if (proofDir == null || proofDir.isEmpty) {
        throw StateError('Missing IAMINA_V101_PROOF_DIR');
      }
      Directory(proofDir).createSync(recursive: true);
      final boundary =
          tester.renderObject<RenderRepaintBoundary>(
              find.byKey(captureKey));
      final image = await boundary.toImage(pixelRatio: 1);
      final data = await image.toByteData(format: ui.ImageByteFormat.png);
      expect(data, isNotNull);
      final png = data!.buffer.asUint8List();
      expect(png.length, greaterThan(5000));
      File(
        '$proofDir/$phase-edit-unit-switch-'
        '${size.width.toInt()}x${size.height.toInt()}.png',
      ).writeAsBytesSync(png);
      image.dispose();
      // Do not wait for a second pump after a render-to-image operation.
      // The test framework owns widget teardown.
    });
  }
  for (final size in <Size>[const Size(390, 844), const Size(768, 1024)]) {
    testWidgets('AddLog unit switch visual proof ${size.width.toInt()}px, $phase',
        (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      final timestamp = DateTime(2026, 9, 20, 10, 30);
      await db.into(db.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const Value(1),
          updatedAt: timestamp,
          unitPreference: const Value('mmol/L'),
        ),
      );
      final profile = await db.select(db.patientProfiles).getSingle();
      final notifier = ValueNotifier<PatientProfileData?>(profile);
      addTearDown(notifier.dispose);
      const key = Key('v101-add-unit-proof-canvas');
      await tester.pumpWidget(
        RepaintBoundary(
          key: key,
          child: ValueListenableBuilder<PatientProfileData?>(
            valueListenable: notifier,
            builder: (_, currentProfile, __) => MaterialApp(
              theme: ThemeData(fontFamily: 'Roboto'),
              locale: const Locale('fr'),
              localizationsDelegates: AppLocalizations.localizationsDelegates,
              supportedLocales: AppLocalizations.supportedLocales,
              home: Scaffold(
                body: MultiProvider(
                  providers: [
                    Provider<AppDatabase>.value(value: db),
                    Provider<PatientProfileData?>.value(value: currentProfile),
                  ],
                  child: const AddLogSheet(),
                ),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final input = find.byKey(const Key('glucose-input'));
      await tester.enterText(input, '4.0');
      await tester.pumpAndSettle();
      notifier.value = profile.copyWith(unitPreference: 'mg/dL');
      await tester.pumpAndSettle();
      final expectedUnit = phase == 'before' ? 'mg/dL' : 'mmol/L';
      expect(tester.widget<TextField>(input).controller!.text, '4.0');
      expect(tester.widget<Text>(find.byKey(const Key('glucose-unit'))).data,
          expectedUnit);
      expect(tester.takeException(), isNull);
      tester.testTextInput.hide();
      await tester.pumpAndSettle();
      final output = Platform.environment['IAMINA_V101_PROOF_DIR'];
      if (output == null || output.isEmpty) {
        throw StateError('Missing IAMINA_V101_PROOF_DIR');
      }
      Directory(output).createSync(recursive: true);
      final image = await tester
          .renderObject<RenderRepaintBoundary>(find.byKey(key))
          .toImage(pixelRatio: 1);
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      expect(bytes, isNotNull);
      final png = bytes!.buffer.asUint8List();
      expect(png.length, greaterThan(5000));
      File(
        '$output/$phase-add-unit-switch-'
        '${size.width.toInt()}x${size.height.toInt()}.png',
      ).writeAsBytesSync(png);
      image.dispose();
      // Do not call pumpWidget during post-image asynchronous teardown.
    });
  }

}
