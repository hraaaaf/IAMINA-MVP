import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:amina/data/models/companion_models.dart';
import 'package:amina/features/companion/companion_screen.dart';
import 'package:amina/services/companion_service.dart';

class _FakeCompanionService extends CompanionService {
  final CompanionOverview overview;

  _FakeCompanionService(this.overview);

  @override
  Future<CompanionOverview?> fetchOverview() async => overview;

  @override
  void dispose() {}
}

CompanionOverview _overview() {
  final now = DateTime.utc(2026, 8, 13, 10);
  return CompanionOverview(
    patternStatus: 'ready',
    reviewStatus: 'ready',
    reviewAnchorCapturedAt: now.subtract(const Duration(days: 7)),
    patterns: [
      CompanionPattern(
        observationKey: 'context:stress',
        currentState: 'active',
        markers: const ['persisting'],
        evidenceDensity: 'moderate',
        recurrenceCount: 2,
        baselineDirection: 'above_personal_window_baseline',
        baselineMovement: 'stable_relative_to_personal_window_baseline',
        firstObservedAt: now.subtract(const Duration(days: 30)),
        lastObservedAt: now,
        evidenceId: 'rule.personal-response.repetition.v1',
        limitations: const ['observational_association_only'],
      ),
    ],
    changesSinceReview: const [
      CompanionChange(
        observationKey: 'context:stress',
        changeKind: 'persisting',
        evidenceStrength: 'moderate',
        missingData: [],
      ),
    ],
    afterVisit: CompanionAfterVisit(
      status: 'recorded',
      anchorId: 4,
      occurredAt: now.subtract(const Duration(days: 2)),
      source: 'after-visit.patient-recorded.v1',
      factCount: 1,
      latestFactAt: now.subtract(const Duration(days: 1)),
    ),
    safetyNotice: 'Server safety copy is intentionally not rendered verbatim.',
    sourceVersion: 'companion-overview.v1',
  );
}

void main() {
  testWidgets('renders patient-first governed companion sections', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: CompanionScreen(service: _FakeCompanionService(_overview())),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Mon compagnon'), findsOneWidget);
    expect(find.text('Ce que vos données montrent'), findsOneWidget);
    expect(find.text('Depuis votre dernière revue'), findsOneWidget);
    expect(find.text('Continuité après consultation'), findsOneWidget);
    expect(find.text('Stress'), findsWidgets);
    expect(find.text('Répétabilité modérée'), findsWidgets);
    expect(
      find.textContaining('Les décisions médicales restent avec votre professionnel de santé.'),
      findsOneWidget,
    );
    expect(find.textContaining('Server safety copy'), findsNothing);
    expect(find.textContaining('médecin virtuel'), findsNothing);
    expect(find.textContaining('modifier votre traitement'), findsNothing);
  });

  testWidgets('renders governed Arabic companion copy in RTL', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('ar'),
        supportedLocales: const [Locale('fr'), Locale('en'), Locale('ar')],
        home: CompanionScreen(service: _FakeCompanionService(_overview())),
      ),
    );
    await tester.pumpAndSettle();

    expect(Directionality.of(tester.element(find.byType(CompanionScreen))), TextDirection.rtl);
    expect(find.text('رفيقي الصحي'), findsOneWidget);
    expect(find.text('ما الذي تظهره بياناتك'), findsOneWidget);
    expect(find.text('منذ آخر مراجعة لك'), findsOneWidget);
    expect(find.text('المتابعة بعد الاستشارة'), findsOneWidget);
    expect(find.text('تكرار متوسط'), findsWidgets);
    expect(find.textContaining('تبقى القرارات الطبية مع طبيبك'), findsOneWidget);
  });
}
