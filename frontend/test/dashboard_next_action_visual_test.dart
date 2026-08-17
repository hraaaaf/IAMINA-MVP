import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/models/companion_next_action_models.dart';
import 'package:amina/features/dashboard/widgets/dashboard_next_action_section.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/companion_service.dart';

const _visualAuditEnabled = bool.fromEnvironment('IAMINA_VISUAL_AUDIT');

class _NextActionVisualService extends CompanionService {
  @override
  Future<CompanionNextAction?> evaluateNextAction() async =>
      const CompanionNextAction(
        status: 'suggested',
        attentionBudget: 'one_non_urgent_item_per_24h',
        pendingCount: 0,
        safetyNotice: 'explicit_visual_fixture',
        suggestion: CompanionNextActionSuggestion(
          suggestionClass: 'PREPARE_CLINICIAN_DISCUSSION',
          observationKey: 'context:stress',
          reason: 'existing_proactive_authority_marks_observation_review_worthy',
          proactiveState: 'persisting',
          changeSinceReview: 'persisting',
          missingData: <String>[],
          limitations: <String>[
            'no_diagnosis_causality_prediction_or_treatment_inference',
          ],
          proactiveSourceVersion: 'proactive.personal-response.lifecycle.v1',
          patternSourceVersion: 'companion-patterns.v1',
          sourceVersion: 'companion-smart-suggestions.v1',
        ),
      );
}

Widget _app({required Locale locale, required CompanionService service, required String keyName}) {
  return MaterialApp(
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
    home: Scaffold(
      backgroundColor: const Color(0xFFF4FBF9),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: RepaintBoundary(
            key: ValueKey<String>(keyName),
            child: DashboardNextActionSection(service: service),
          ),
        ),
      ),
    ),
  );
}

Future<void> _captureActive(
  WidgetTester tester, {
  required Size size,
  required Locale locale,
  required String name,
}) async {
  final service = _NextActionVisualService();
  addTearDown(service.dispose);
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  await tester.pumpWidget(_app(locale: locale, service: service, keyName: name));
  await tester.pumpAndSettle();

  expect(find.byKey(const ValueKey('dashboard-next-action-prepare')), findsOneWidget);
  expect(find.byKey(const ValueKey('dashboard-next-action-result-title')), findsNothing);
  await tester.tap(find.byKey(const ValueKey('dashboard-next-action-prepare')));
  await tester.pumpAndSettle();

  expect(find.byKey(const ValueKey('dashboard-next-action-result-title')), findsOneWidget);
  expect(find.byKey(const ValueKey('dashboard-next-action-open')), findsOneWidget);
  await expectLater(
    find.byKey(ValueKey<String>(name)),
    matchesGoldenFile('ui_audit_output/$name.png'),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('next action renders only after explicit tap in FR', (tester) async {
    if (!_visualAuditEnabled) return;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    await _captureActive(
      tester,
      size: const Size(390, 844),
      locale: const Locale('fr'),
      name: 'dashboard-next-action-390x844',
    );
  });

  testWidgets('next action renders only after explicit tap in AR RTL', (tester) async {
    if (!_visualAuditEnabled) return;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    await _captureActive(
      tester,
      size: const Size(360, 560),
      locale: const Locale('ar'),
      name: 'dashboard-next-action-ar-360x560',
    );
  });
}
