import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/features/dashboard/widgets/agp_chart.dart';
import 'package:amina/features/journal/ai_summary_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  Future<void> render(WidgetTester tester, String mode, {Size size = const Size(390, 844), Locale locale = const Locale('fr')}) async {
    await tester.binding.setSurfaceSize(size);
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      ChangeNotifierProvider<TweaksNotifier>(
        create: (_) => TweaksNotifier(),
        child: MaterialApp(
          locale: locale,
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

  for (final size in <Size>[const Size(390, 844), const Size(768, 1024)]) {
    testWidgets('verified CGM chart paints at ${size.width.toInt()}px', (tester) async {
      await render(tester, 'agp-verified', size: size);
      expect(find.text('25–75%'), findsOneWidget);
      expect(find.text('5–95%'), findsOneWidget);
      expect(find.text('Données insuffisantes.'), findsNothing);
      final chart = find.byWidgetPredicate(
        (widget) => widget is CustomPaint && widget.painter is AgpPainter,
      );
      expect(chart, findsOneWidget);
      final chartSize = tester.getSize(chart);
      expect(chartSize.width, greaterThan(100));
      expect(chartSize.height, greaterThan(100));
      final painter = tester.widget<CustomPaint>(chart).painter! as AgpPainter;
      expect(painter.points.length, 24);
      expect(tester.takeException(), isNull);
    });
  }
  testWidgets('verified CGM chart supports Arabic RTL', (tester) async {
    await render(tester, 'agp-verified', locale: const Locale('ar'));
    expect(find.text('25–75%'), findsOneWidget);
    expect(find.text('5–95%'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('AGP does not render invented 100% breakdown from manual logs', (tester) async {
    await render(tester, 'agp');
    expect(find.text('100%'), findsNothing);
    // Even if raw manual-only percentile points exist, no AGP legend.
    expect(find.text('25–75%'), findsNothing);
    expect(find.text('5–95%'), findsNothing);
    // The AGP panel uses the localized extension copy (with a period),
    // not the Dashboard-specific insufficiency caption.
    expect(find.text('Données insuffisantes.'), findsOneWidget);
  });
}
