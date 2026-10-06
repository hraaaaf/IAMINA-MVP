import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/proactive_preview_models.dart';
import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/features/dashboard/widgets/dashboard_insight_section.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/routes/app_router.dart';
import 'package:amina/services/companion_service.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class _FirstUseCompanionService extends CompanionService {
  @override
  Future<ProactivePreview?> fetchProactivePreview() async =>
      const ProactivePreview(
        status: 'insufficient_data',
        attentionBudget: 'one_non_urgent_item_per_24h',
        cooldownUntil: null,
        pendingCount: 0,
        safetyNotice: 'first_use_certification',
        item: null,
      );

  @override
  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) async =>
      const CompanionChatReply(
        reply:
            'Je peux t’aider à organiser ce que tu as enregistré, sans inventer ce que les données ne montrent pas.',
        conversationId: 'first-use-cert',
        replyLanguage: 'fr',
      );

  @override
  void dispose() {}
}

Widget _localized(Widget child) => MaterialApp(
  locale: const Locale('fr'),
  localizationsDelegates: const [
    AppLocalizations.delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(body: child),
);

void _mobile(WidgetTester tester) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = const Size(390, 844);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('first-use routing requires minimum onboarding before consent', () {
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: false,
        hasProfileState: true,
      ),
      isTrue,
    );
    expect(
      shouldApplyConsentGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasConsentService: true,
      ),
      isTrue,
    );
  });

  testWidgets(
    'virgin local data reaches first factual value without fabricated insight',
    (tester) async {
      _mobile(tester);
      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);

      expect(await db.countLogs(), 0);

      await tester.pumpWidget(
        _localized(
          MultiProvider(
            providers: [
              Provider<AppDatabase>.value(value: db),
              Provider<PatientProfileData?>.value(value: null),
            ],
            child: const AddLogSheet(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(
        find.text('Aucune valeur n’est supposée avant ta saisie.'),
        findsOneWidget,
      );

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.pump();
      await tester.tap(find.byKey(const Key('save-log-button')));
      await tester.pumpAndSettle();

      final logs = await db.select(db.logEntries).get();
      expect(logs, hasLength(1));
      expect(logs.single.bloodSugar, 126);
      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
      expect(find.textContaining('126 mg/dL'), findsOneWidget);
      expect(
        find.textContaining('n’interprète pas la mesure'),
        findsOneWidget,
      );

      final companion = _FirstUseCompanionService();
      await tester.pumpWidget(
        _localized(
          MultiProvider(
            providers: [Provider<AppDatabase>.value(value: db)],
            child: DashboardInsightSection(service: companion),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      final l10n = AppLocalizations.of(
        tester.element(find.byType(DashboardInsightSection)),
      )!;
      expect(find.text(l10n.dashboardInsightInsufficient), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('first IAmina exchange works after first-use value', (tester) async {
    _mobile(tester);
    final service = _FirstUseCompanionService();

    await tester.pumpWidget(
      MaterialApp(
        home: CompanionConversationScreen(service: service),
      ),
    );
    await tester.pump();

    await tester.enterText(
      find.byKey(const Key('companion-chat-input')),
      'Que peux-tu faire avec cette première mesure ?',
    );
    await tester.tap(find.byKey(const Key('companion-chat-send')));
    await tester.pumpAndSettle();

    expect(
      find.text('Que peux-tu faire avec cette première mesure ?'),
      findsOneWidget,
    );
    expect(
      find.textContaining('sans inventer ce que les données ne montrent pas'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
}
