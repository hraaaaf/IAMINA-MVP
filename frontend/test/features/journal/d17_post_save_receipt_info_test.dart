import 'package:amina/features/journal/widgets/post_save_receipt.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

Widget receipt(Locale locale, {VoidCallback? onDone}) => MaterialApp(
  locale: locale,
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(
    body: PostSaveReceipt(
      data: const PostSaveReceiptData(
        glucose: 126,
        unit: 'mg/dL',
        timeLabel: '02/11 · 10:30',
        measurementContextLabel: 'Before meal',
        mealTypeLabel: 'Lunch',
        insulinUnits: 4,
        additionalContextLabels: <String>['Stressed'],
      ),
      onViewJournal: () {},
      onAddAnother: () {},
      onDone: onDone ?? () {},
    ),
  ),
);

void main() {
  for (final locale in const <Locale>[Locale('fr'), Locale('ar')]) {
    for (final size in const <Size>[
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      testWidgets('D17 real saved receipt: essential facts remain visible; info toggles '
          '${locale.languageCode} ${size.width}x${size.height}', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        await tester.pumpWidget(receipt(locale));
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('d17-receipt-info')), findsOneWidget);
        expect(find.byKey(const Key('d17-receipt-help')), findsNothing);
        final semanticInfo = find.ancestor(
          of: find.byKey(const Key('d17-receipt-info')),
          matching: find.byType(Semantics),
        ).first;
        final closedSemantics = tester.widget<Semantics>(semanticInfo);
        expect(closedSemantics.properties.toggled, isFalse);
        expect(
          closedSemantics.properties.label,
          contains(locale.languageCode == 'fr'
              ? 'Afficher les informations'
              : 'عرض المعلومات'),
        );
        expect(find.text('126 mg/dL'), findsOneWidget);
        expect(find.text('02/11 · 10:30'), findsOneWidget);
        expect(find.byKey(const Key('post-save-view-journal')), findsOneWidget);
        expect(find.byKey(const Key('post-save-add-another')), findsOneWidget);
        expect(find.byKey(const Key('post-save-done')), findsOneWidget);
        expect(
          find.text(locale.languageCode == 'fr'
              ? 'Mesure enregistrée.'
              : 'تم حفظ القياس.'),
          findsOneWidget,
        );
        expect(
          find.text(locale.languageCode == 'fr'
              ? 'Enregistrée sur cet appareil.'
              : 'تم الحفظ على هذا الجهاز.'),
          findsOneWidget,
        );
        expect(tester.takeException(), isNull);

        final info = find.byKey(const Key('d17-receipt-info'));
        await tester.ensureVisible(info);
        await tester.tap(info);
        await tester.pumpAndSettle();
        expect(find.byKey(const Key('d17-receipt-help')), findsOneWidget);
        final openedSemantics = tester.widget<Semantics>(semanticInfo);
        expect(openedSemantics.properties.toggled, isTrue);
        final help = tester.widget<Padding>(
          find.byKey(const Key('d17-receipt-help')),
        );
        expect(help.child, isA<Text>());
        expect(
          (help.child! as Text).data,
          contains(locale.languageCode == 'fr'
              ? 'Elle n’interprète pas la mesure.'
              : 'ولا يفسّر القياس.'),
        );
        expect(find.text('126 mg/dL'), findsOneWidget);
        expect(tester.takeException(), isNull);

        await tester.tap(info);
        await tester.pumpAndSettle();
        expect(find.byKey(const Key('d17-receipt-help')), findsNothing);
        expect(find.text('126 mg/dL'), findsOneWidget);
        expect(tester.takeException(), isNull);
      });
    }
  }

  testWidgets('D17 keyboard Tab and Enter open the saved receipt explanation',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(receipt(const Locale('fr')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d17-receipt-help')), findsNothing);
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.pump();
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d17-receipt-help')), findsOneWidget);
    expect(find.text('126 mg/dL'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('D17 desktop hover provides the same technical explanation',
      (tester) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(receipt(const Locale('en')));
    await tester.pumpAndSettle();
    final info = find.byKey(const Key('d17-receipt-info'));
    final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
    await mouse.addPointer(location: Offset.zero);
    await mouse.moveTo(tester.getCenter(info));
    await tester.pump(const Duration(seconds: 2));
    expect(find.textContaining('This confirmation only describes what was saved.'),
        findsWidgets);
    expect(find.byKey(const Key('d17-receipt-help')), findsNothing);
    expect(find.text('126 mg/dL'), findsOneWidget);
    await mouse.removePointer();
    expect(tester.takeException(), isNull);
  });
}
