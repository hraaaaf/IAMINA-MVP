import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/companion_models.dart';
import 'package:amina/data/models/proactive_preview_models.dart';
import 'package:amina/features/dashboard/dashboard_companion_entry_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/companion_service.dart';

const _visualAuditEnabled = bool.fromEnvironment('IAMINA_VISUAL_AUDIT');

class _ResponsiveCompanionService extends CompanionService {
  @override
  Future<CompanionOverview?> fetchOverview() async => CompanionOverview(
    patternStatus: 'ready',
    reviewStatus: 'ready',
    reviewAnchorCapturedAt: DateTime.utc(2026, 8, 15, 10),
    patterns: const <CompanionPattern>[],
    changesSinceReview: const <CompanionChange>[
      CompanionChange(
        observationKey: 'meal:lunch',
        changeKind: 'persisting',
        evidenceStrength: 'moderate',
        missingData: <String>[],
      ),
    ],
    afterVisit: const CompanionAfterVisit(
      status: 'no_recorded_visit',
      anchorId: null,
      occurredAt: null,
      source: null,
      factCount: 0,
      latestFactAt: null,
    ),
    safetyNotice: 'responsive_visual_fixture',
    sourceVersion: 'ui-responsive-audit.v1',
  );

  @override
  Future<ProactivePreview?> fetchProactivePreview() async => const ProactivePreview(
    status: 'available',
    attentionBudget: 'one_non_urgent_item_per_24h',
    cooldownUntil: null,
    pendingCount: 1,
    safetyNotice: 'responsive_preview_fixture',
    item: ProactivePreviewItem(
      observationKey: 'context:stress',
      kind: 'context',
      state: 'persisting',
      surfaceNow: false,
      whatChanged: 'repeated_eligible_evidence',
      whyItIsSurfacingNow: 'persistence_or_evidence_density_changed',
      evidenceWindowDays: 90,
      personalBaselineComparisonMgDl: 24,
      observations: 6,
      distinctDays: 4,
      evidenceDensity: 'moderate',
      limitationsOrMissingData: <String>['observational_association_only'],
      allowedNextStep: 'PREPARE_CLINICIAN_DISCUSSION',
      escalationClass: 'none',
      evidenceId: 'rule.personal-response.repetition.v1',
      sourceVersion: 'proactive.personal-response.lifecycle.v1',
      priority: ProactivePreviewPriority(
        safetyTimeSensitivity: 'non_urgent_observation',
        clinicalRelevance: 'review_worthy',
        persistence: 'recurrent_episode',
        changeFromPersonalBaselineMgDl: 24,
        evidenceDensity: 'moderate',
        actionability: 'PREPARE_CLINICIAN_DISCUSSION',
        evidenceMaturity: 'internal_governed_rule',
        interruptionCost: 'eligible',
      ),
    ),
  );
}

Future<void> _capture(
  WidgetTester tester, {
  required Size size,
  required Locale locale,
  required String name,
}) async {
  final db = AppDatabase(NativeDatabase.memory());
  final service = _ResponsiveCompanionService();
  await db.seedDemoData();
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  try {
    await tester.pumpWidget(
      Provider<AppDatabase>.value(
        value: db,
        child: MaterialApp(
          debugShowCheckedModeBanner: false,
          theme: AminaVisualLanguage.harmonize(AminaTheme.light),
          locale: locale,
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          home: RepaintBoundary(
            key: ValueKey<String>(name),
            child: DashboardCompanionEntryScreen(companionService: service),
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 1800));
    await expectLater(
      find.byKey(ValueKey<String>(name)),
      matchesGoldenFile('ui_audit_output/$name.png'),
    );
  } finally {
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
    await db.close();
    service.dispose();
    await tester.pump();
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Dashboard stays one product across former 700px fork and desktop', (
    tester,
  ) async {
    if (!_visualAuditEnabled) return;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    await _capture(
      tester,
      size: const Size(699, 900),
      locale: const Locale('fr'),
      name: 'dashboard-responsive-699x900',
    );
    await _capture(
      tester,
      size: const Size(701, 900),
      locale: const Locale('fr'),
      name: 'dashboard-responsive-701x900',
    );
    await _capture(
      tester,
      size: const Size(1440, 1000),
      locale: const Locale('fr'),
      name: 'dashboard-responsive-1440x1000',
    );
    await _capture(
      tester,
      size: const Size(900, 900),
      locale: const Locale('ar'),
      name: 'dashboard-responsive-ar-900x900',
    );
  });
}
