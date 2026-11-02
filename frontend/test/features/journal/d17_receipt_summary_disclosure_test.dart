import 'package:amina/features/journal/widgets/post_save_receipt.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final locale in const <Locale>[Locale('fr'), Locale('ar')]) {
    for (final viewport in const <Size>[
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      testWidgets(
        'D17 receipt summary info is optional, not clinical data '
        '${locale.languageCode} $viewport',
        (tester) async {
          tester.view.physicalSize = viewport;
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);

          var journalOpens = 0;
          var anotherOpens = 0;
          var doneCalls = 0;

          await tester.pumpWidget(
            MaterialApp(
              locale: locale,
              supportedLocales: AppLocalizations.supportedLocales,
              localizationsDelegates: AppLocalizations.localizationsDelegates,
              home: PostSaveReceipt(
                data: const PostSaveReceiptData(
                  glucose: 126,
                  unit: 'mg/dL',
                  timeLabel: '02/11 · 10:30',
                  measurementContextLabel: 'Après repas',
                  mealTypeLabel: 'Déjeuner',
                  additionalContextLabels: <String>['Stress'],
                ),
                onViewJournal: () => journalOpens++,
                onAddAnother: () => anotherOpens++,
                onDone: () => doneCalls++,
              ),
            ),
          );
          await tester.pumpAndSettle();

          final l10n = AppLocalizations.of(
            tester.element(find.byType(PostSaveReceipt)),
          )!;
          final info = find.byKey(const Key('d17-entry-summary-info'));

          // The D17 description alone is folded away. Neither recorded
          // measurements nor save status nor navigation are gated by it.
          expect(info, findsOneWidget);
          expect(
            find.byKey(const Key('d17-entry-summary-details')),
            findsNothing,
          );
          expect(find.text(l10n.journalPostSaveSummaryTitle), findsOneWidget);
          expect(find.text(l10n.journalSaved), findsOneWidget);
          expect(find.text(l10n.journalPostSaveDeviceStatus), findsOneWidget);
          expect(find.text('126 mg/dL'), findsOneWidget);
          expect(find.text('02/11 · 10:30'), findsOneWidget);
          expect(find.textContaining('Après repas'), findsOneWidget);
          expect(find.textContaining('Déjeuner'), findsOneWidget);
          expect(find.byKey(const Key('post-save-view-journal')), findsOneWidget);
          expect(find.byKey(const Key('post-save-add-another')), findsOneWidget);
          expect(find.byKey(const Key('post-save-done')), findsOneWidget);
          expect(tester.takeException(), isNull);

          final hoverHelp = tester.widget<Tooltip>(
            find.ancestor(of: info, matching: find.byType(Tooltip)).first,
          );
          expect(hoverHelp.message, l10n.journalPostSaveNotice);

          await tester.ensureVisible(info);
          await tester.tap(info);
          await tester.pumpAndSettle();
          expect(
            find.byKey(const Key('d17-entry-summary-details')),
            findsOneWidget,
          );
          expect(find.text(l10n.journalPostSaveNotice), findsOneWidget);
          // Clinical data and actions remain visible after disclosure.
          expect(find.text('126 mg/dL'), findsOneWidget);
          expect(find.text(l10n.journalPostSaveDeviceStatus), findsOneWidget);
          expect(tester.takeException(), isNull);

          await tester.tap(info);
          await tester.pumpAndSettle();
          expect(
            find.byKey(const Key('d17-entry-summary-details')),
            findsNothing,
          );
          expect(find.text('126 mg/dL'), findsOneWidget);
          expect(tester.takeException(), isNull);

          await tester.ensureVisible(
            find.byKey(const Key('post-save-view-journal')),
          );
          await tester.tap(find.byKey(const Key('post-save-view-journal')));
          expect(journalOpens, 1);
          expect(anotherOpens, 0);
          expect(doneCalls, 0);
        },
      );
    }
  }
}
