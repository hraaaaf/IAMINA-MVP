import 'package:amina/core/widgets/amina_text_field.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/features/profile/profile_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/consent_service.dart';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  for (final size in <Size>[const Size(390, 844), const Size(768, 1024)]) {
    testWidgets('Profile targets stay canonical across unit selection '
        '${size.width.toInt()}px', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      await db.into(db.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const Value(1),
          updatedAt: DateTime(2026, 9, 20),
          diabetesType: const Value('type2'),
          treatment: const Value('lifestyle'),
          unitPreference: const Value('mmol/L'),
          targetRangeLow: const Value(69.9),
          targetRangeHigh: const Value(180.0),
        ),
      );
      final profile = await db.select(db.patientProfiles).getSingle();
      final consent = ConsentService()..seedInitialProfile(profile);
      addTearDown(consent.dispose);

      await tester.pumpWidget(
        MaterialApp(
          locale: const Locale('fr'),
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          home: MultiProvider(
            providers: [
              Provider<AppDatabase>.value(value: db),
              ChangeNotifierProvider<ConsentService>.value(value: consent),
              ChangeNotifierProvider<AuthService>(
                create: (_) => AuthService(),
              ),
            ],
            child: const ProfileScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final medicalSection =
          find.byKey(const ValueKey('profile-medical-section'));
      await tester.ensureVisible(medicalSection);
      await tester.pumpAndSettle();
      await tester.tap(find.descendant(
        of: medicalSection,
        matching: find.byType(ExpansionTile),
      ));
      await tester.pumpAndSettle();

      Finder unitFields(String unit) => find.byWidgetPredicate(
        (widget) =>
            widget is AminaTextField && widget.label.contains('($unit)'),
      );
      List<String> values(String unit) => tester
          .widgetList<AminaTextField>(unitFields(unit))
          .map((w) => w.controller.text)
          .toList();

      expect(values('mmol/L'), <String>['3.9', '10.0']);

      final mgChoice = find.text('mg/dL').last;
      await tester.ensureVisible(mgChoice);
      await tester.pumpAndSettle();
      await tester.tap(mgChoice);
      await tester.pumpAndSettle();
      expect(values('mg/dL'), <String>['70', '180']);

      final mmolChoice = find.text('mmol/L').last;
      await tester.ensureVisible(mmolChoice);
      await tester.pumpAndSettle();
      await tester.tap(mmolChoice);
      await tester.pumpAndSettle();
      expect(values('mmol/L'), <String>['3.9', '10.0']);

      final save = find.byKey(const Key('profile-save-targets-button'));
      await tester.ensureVisible(save);
      await tester.pumpAndSettle();
      await tester.tap(save);
      await tester.pumpAndSettle();
      var stored = await db.select(db.patientProfiles).getSingle();
      expect(stored.targetRangeLow, closeTo(69.9, 1e-9));
      expect(stored.targetRangeHigh, 180.0);

      final targetFields = unitFields('mmol/L');
      final lowInput = find.descendant(
        of: targetFields.at(0),
        matching: find.byType(TextField),
      );
      final highInput = find.descendant(
        of: targetFields.at(1),
        matching: find.byType(TextField),
      );
      expect(
        tester.widget<TextField>(lowInput).keyboardType,
        const TextInputType.numberWithOptions(decimal: true),
      );
      await tester.ensureVisible(lowInput);
      await tester.enterText(lowInput, '4.0');
      await tester.ensureVisible(highInput);
      await tester.enterText(highInput, '10.5');
      tester.testTextInput.hide();
      await tester.pumpAndSettle();
      await tester.ensureVisible(save);
      await tester.pumpAndSettle();
      await tester.tap(save);
      await tester.pumpAndSettle();
      stored = await db.select(db.patientProfiles).getSingle();
      expect(stored.targetRangeLow, closeTo(72.064, 1e-7));
      expect(stored.targetRangeHigh, closeTo(189.168, 1e-7));
      // If a mobile RenderFlex overflows, surface its full diagnostics.
      // A generic expect(takeException(), isNull) hides the owning widget.
      final renderException = tester.takeException();
      if (renderException != null) {
        if (renderException is FlutterError) {
          debugPrint('V101_PROFILE_RENDER_TRACE: ${renderException.toStringDeep()}');
          // Diagnostic from concrete RenderFlex layout, not assumptions.
          for (final element in tester.allElements) {
            final render = element.renderObject;
            if (render is! RenderFlex ||
                render.direction != Axis.horizontal ||
                !render.hasSize) {
              continue;
            }
            double maxRight = 0;
            RenderBox? child = render.firstChild;
            while (child != null) {
              if (child.hasSize && child.parentData is FlexParentData) {
                final offset = (child.parentData! as FlexParentData).offset;
                final edge = offset.dx + child.size.width;
                if (edge > maxRight) maxRight = edge;
              }
              child = render.childAfter(child);
            }
            if (maxRight > render.size.width + 1) {
              debugPrint(
                'V101_OVERFLOW_ROW width=${render.size.width.toStringAsFixed(1)} '
                'edge=${maxRight.toStringAsFixed(1)} '
                'widget=${element.widget.runtimeType} '
                'creator=${render.debugCreator}',
              );
            }
          }
        } else {
          debugPrint('V101_PROFILE_RENDER_TRACE: $renderException');
        }
        fail('Profile layout error at ${size.width.toInt()}px: $renderException');
      }
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
    });
  }

  testWidgets('Profile does not save unknown glucose unit', (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const Value(1),
        updatedAt: DateTime(2026, 9, 20),
        diabetesType: const Value('type2'),
        treatment: const Value('lifestyle'),
        unitPreference: const Value('not-a-unit'),
        targetRangeLow: const Value(70),
        targetRangeHigh: const Value(180),
      ),
    );
    final profile = await db.select(db.patientProfiles).getSingle();
    final consent = ConsentService()..seedInitialProfile(profile);
    addTearDown(consent.dispose);
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            ChangeNotifierProvider<ConsentService>.value(value: consent),
            ChangeNotifierProvider<AuthService>(
              create: (_) => AuthService(),
            ),
          ],
          child: const ProfileScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();
    final section = find.byKey(const ValueKey('profile-medical-section'));
    await tester.ensureVisible(section);
    await tester.pumpAndSettle();
    await tester.tap(find.descendant(
      of: section,
      matching: find.byType(ExpansionTile),
    ));
    await tester.pumpAndSettle();
    final save = find.byKey(const Key('profile-save-targets-button'));
    await tester.ensureVisible(save);
    await tester.tap(save);
    await tester.pumpAndSettle();
    final stored = await db.select(db.patientProfiles).getSingle();
    expect(stored.unitPreference, 'not-a-unit');
    expect(stored.targetRangeLow, 70);
    expect(stored.targetRangeHigh, 180);
  });
}
