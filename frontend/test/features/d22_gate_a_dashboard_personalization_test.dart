import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/companion_models.dart';
import 'package:amina/data/models/companion_next_action_models.dart';
import 'package:amina/data/models/proactive_preview_models.dart';
import 'package:amina/features/dashboard/widgets/dashboard_insight_section.dart';
import 'package:amina/features/dashboard/widgets/dashboard_next_action_section.dart';
import 'package:amina/features/dashboard/widgets/dashboard_responsive_sections.dart';
import 'package:amina/features/dashboard/widgets/dashboard_today_section.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/companion_service.dart';

class _CountingCompanionService extends CompanionService {
  int overviewCalls = 0;
  int previewCalls = 0;
  int actionCalls = 0;

  @override
  Future<CompanionOverview?> fetchOverview() async {
    overviewCalls++;
    return null;
  }

  @override
  Future<ProactivePreview?> fetchProactivePreview() async {
    previewCalls++;
    return null;
  }

  @override
  Future<CompanionNextAction?> evaluateNextAction() async {
    actionCalls++;
    return null;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  for (final locale in const [Locale('fr'), Locale('ar')]) {
    testWidgets('D22 Gate A dashboard blocks personalized calls in ${locale.languageCode}',
        (tester) async {
      final db = AppDatabase(NativeDatabase.memory());
      final service = _CountingCompanionService();
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = const Size(390, 844);

      // Keep Drift stream cleanup inside testWidgets' fake-async zone.
      // Previous teardown awaited db.close() while a zero-delay Drift
      // StreamQueryStore cancellation timer was still pending.
      try {
        await tester.pumpWidget(
          Provider<AppDatabase>.value(
            value: db,
            child: MaterialApp(
              locale: locale,
              localizationsDelegates: const [
                AppLocalizations.delegate,
                GlobalMaterialLocalizations.delegate,
                GlobalWidgetsLocalizations.delegate,
                GlobalCupertinoLocalizations.delegate,
              ],
              supportedLocales: AppLocalizations.supportedLocales,
              home: Scaffold(
                body: SingleChildScrollView(
                  child: Column(
                    children: [
                      DashboardTodaySection(
                        targetConfigured: false,
                        service: service,
                      ),
                      DashboardResponsiveSections(
                        unit: 'mg/dL',
                        low: null,
                        high: null,
                        companionService: service,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 250));

        expect(service.overviewCalls, 0);
        expect(service.previewCalls, 0);
        expect(service.actionCalls, 0);
        expect(find.byType(DashboardInsightSection), findsNothing);
        expect(find.byType(DashboardNextActionSection), findsNothing);
        expect(find.byKey(const ValueKey('d22-dashboard-personalization-blocked')),
            findsOneWidget);
        if (locale.languageCode == 'fr') {
          expect(find.textContaining('objectifs glycémiques non vérifiés'),
              findsWidgets);
        } else {
          expect(find.textContaining('أهداف سكر الدم غير مؤكدة'), findsWidgets);
        }
      } finally {
        // Unmount all StreamBuilders and flush Drift's cancellation timer
        // before closing the local database, as in the passing dashboard
        // responsive visual test.
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.pump(const Duration(milliseconds: 1));
        await db.close();
        service.dispose();
        await tester.pump(const Duration(milliseconds: 1));
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      }
    });
  }
}
