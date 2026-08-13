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

void main() {
  testWidgets('renders patient-first governed companion sections', (tester) async {
    final now = DateTime.utc(2026, 8, 13, 10);
    final overview = CompanionOverview(
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
      safetyNotice: 'Companion support only. Medical decisions remain with your clinician.',
      sourceVersion: 'companion-overview.v1',
    );

    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        home: CompanionScreen(service: _FakeCompanionService(overview)),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Mon compagnon'), findsOneWidget);
    expect(find.text('Ce que vos données montrent'), findsOneWidget);
    expect(find.text('Depuis votre dernière revue'), findsOneWidget);
    expect(find.text('Continuité après consultation'), findsOneWidget);
    expect(find.text('Stress'), findsWidgets);
    expect(find.textContaining('médecin virtuel'), findsNothing);
    expect(find.textContaining('modifier votre traitement'), findsNothing);
  });
}
