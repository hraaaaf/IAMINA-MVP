import 'package:amina/features/dashboard/widgets/add_log_view.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final locale in const <Locale>[Locale('fr'), Locale('ar')]) {
    for (final size in const <Size>[
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      testWidgets('D17 secondary info remains accessible ${locale.languageCode} $size', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        var dateEdits = 0;
        var sickUpdates = 0;
        await tester.pumpWidget(MaterialApp(
          locale: locale,
          supportedLocales: AppLocalizations.supportedLocales,
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          home: Scaffold(
            body: SingleChildScrollView(
              child: AddLogDetailsCard(
                timeLabel: '02/11 · 10:30',
                onPickDateTime: () async { dateEdits++; },
                isSick: false,
                isStressed: false,
                isActive: false,
                badSleep: false,
                onSickChanged: (_) { sickUpdates++; },
                onStressedChanged: (_) {},
                onActiveChanged: (_) {},
                onBadSleepChanged: (_) {},
              ),
            ),
          ),
        ));
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('d17-details-info')), findsOneWidget);
        expect(find.byKey(const Key('d17-details-help')), findsNothing);
        expect(find.byKey(const Key('journal-context-selector')), findsOneWidget);
        expect(find.text('02/11 · 10:30'), findsOneWidget);
        expect(tester.takeException(), isNull);

        await tester.tap(find.byKey(const Key('d17-details-info')));
        await tester.pumpAndSettle();
        expect(find.byKey(const Key('d17-details-help')), findsOneWidget);
        expect(find.byKey(const Key('journal-context-selector')), findsOneWidget);
        expect(tester.takeException(), isNull);

        await tester.tap(find.byKey(const Key('d17-details-info')));
        await tester.pumpAndSettle();
        expect(find.byKey(const Key('d17-details-help')), findsNothing);
        final dt = find.text('02/11 · 10:30');
        await tester.ensureVisible(dt);
        await tester.tap(dt);
        expect(dateEdits, 1);
        final sick = find.byKey(const Key('context-illness'));
        await tester.ensureVisible(sick);
        await tester.tap(sick);
        expect(sickUpdates, 1);
        expect(tester.takeException(), isNull);
      });
    }
  }
}
