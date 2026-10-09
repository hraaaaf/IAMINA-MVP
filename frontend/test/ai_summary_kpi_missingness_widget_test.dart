import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/features/journal/ai_summary_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  Future<void> render(WidgetTester tester, String mode) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      ChangeNotifierProvider<TweaksNotifier>(
        create: (_) => TweaksNotifier(),
        child: MaterialApp(
          locale: const Locale('fr'),
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          home: AISummaryKpiVisualFixture(mode: mode),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }

  testWidgets('manual-only readings do not turn unavailable CGM KPIs into zero', (tester) async {
    await render(tester, 'cards');
    expect(find.text('Non disponible'), findsNWidgets(3));
    expect(find.text('0%'), findsNothing);
    expect(find.text('0.0%'), findsNothing);
    expect(find.text('Données insuffisantes'), findsNWidgets(3));
  });

  testWidgets('hero makes no adverse target judgment with missing CGM proof', (tester) async {
    await render(tester, 'hero');
    expect(find.text('Données insuffisantes'), findsOneWidget);
    expect(find.textContaining('à revoir'), findsNothing);
  });

  testWidgets('AGP does not render invented 100% breakdown from manual logs', (tester) async {
    await render(tester, 'agp');
    expect(find.text('100%'), findsNothing);
    // The AGP panel uses the localized extension copy (with a period),
    // not the Dashboard-specific insufficiency caption.
    expect(find.text('Données insuffisantes.'), findsOneWidget);
  });
}
