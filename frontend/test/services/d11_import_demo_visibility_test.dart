import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/features/import/import_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Future<void> renderImport(WidgetTester tester, AppDatabase db) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    await tester.pumpWidget(
      Provider<AppDatabase>.value(
        value: db,
        child: const MaterialApp(
          locale: Locale('fr'),
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          home: ImportScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('D11: patient import has no DEV demo seed action', (tester) async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734));
    addTearDown(db.close);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await renderImport(tester, db);
    expect(find.byType(ImportScreen), findsOneWidget);
    expect(find.text('DEV'), findsNothing);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });

  testWidgets('D11: audit import exposes isolated demo fixture', (tester) async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly());
    addTearDown(db.close);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await renderImport(tester, db);
    expect(find.byType(ImportScreen), findsOneWidget);
    expect(find.text('DEV'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });
}
