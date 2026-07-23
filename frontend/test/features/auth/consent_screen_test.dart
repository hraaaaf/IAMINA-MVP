// ConsentScreen — widget tests
//
// Verifies the RGPD consent gate renders correctly and responds to user actions.
// ApiClient calls are mocked; navigation is captured via GoRouter's redirect.
import 'dart:async';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';
import 'package:provider/provider.dart';
import 'package:amina/features/auth/consent_screen.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/consent_service.dart';
import '../../mocks.dart';

// ── Helpers ───────────────────────────────────────────────────────────────────

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

class _FakeConsentService extends Fake implements ConsentService {
  bool _declined = false;
  @override bool get hasConsent => false;
  @override bool get hasDeclinedLocally => _declined;
  @override void declineLocally() => _declined = true;
  @override void addListener(VoidCallback listener) {}
  @override void removeListener(VoidCallback listener) {}
  @override void dispose() {}
}

/// Wraps ConsentScreen in a minimal testable app.
/// [onNavigate] receives every GoRouter location change.
Widget _makeApp({
  required AppDatabase db,
  required ApiClient apiClient,
  required ConsentService consentService,
  void Function(String path)? onNavigate,
}) {
  final navigated = <String>[];

  final router = GoRouter(
    initialLocation: '/consent',
    routes: [
      GoRoute(
        path: '/consent',
        builder: (_, __) => const ConsentScreen(),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (_, __) => const Scaffold(body: Text('Dashboard')),
      ),
    ],
    observers: [
      _NavigationObserver((path) {
        navigated.add(path);
        onNavigate?.call(path);
      }),
    ],
  );

  return MultiProvider(
    providers: [
      Provider<AppDatabase>.value(value: db),
      Provider<ApiClient>.value(value: apiClient),
      ChangeNotifierProvider<ConsentService>.value(value: consentService),
    ],
    child: MaterialApp.router(
      routerConfig: router,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [Locale('fr'), Locale('ar', 'MA')],
    ),
  );
}

class _NavigationObserver extends NavigatorObserver {
  final void Function(String path) onPush;
  _NavigationObserver(this.onPush);

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    final name = route.settings.name ?? '';
    onPush(name);
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late AppDatabase db;
  late MockApiClient mockApi;
  late _FakeConsentService consentService;

  setUpAll(() {
    registerFallbackValue('');
  });

  setUp(() {
    db = _openDb();
    mockApi = MockApiClient();
    consentService = _FakeConsentService();

    // Default: giveConsent returns success
    when(() => mockApi.giveConsent()).thenAnswer((_) async => true);
  });

  tearDown(() async {
    await db.close();
  });

  // ── Rendering ────────────────────────────────────────────────────────────────

  testWidgets('renders without error (smoke test)', (tester) async {
    await tester.pumpWidget(_makeApp(
      db: db, apiClient: mockApi, consentService: consentService,
    ));
    await tester.pumpAndSettle();
    expect(find.byType(ConsentScreen), findsOneWidget);
  });

  testWidgets('shows shield icon in header', (tester) async {
    await tester.pumpWidget(_makeApp(
      db: db, apiClient: mockApi, consentService: consentService,
    ));
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.shield_outlined), findsOneWidget);
  });

  testWidgets('shows accept button', (tester) async {
    await tester.pumpWidget(_makeApp(
      db: db, apiClient: mockApi, consentService: consentService,
    ));
    await tester.pumpAndSettle();
    // l10n key: consentAccept
    expect(
      find.textContaining('Accepter').evaluate().isNotEmpty ||
      find.textContaining('Accept').evaluate().isNotEmpty,
      isTrue,
    );
  });

  testWidgets('shows decline button', (tester) async {
    await tester.pumpWidget(_makeApp(
      db: db, apiClient: mockApi, consentService: consentService,
    ));
    await tester.pumpAndSettle();
    // l10n key: consentDeclineWithoutAI
    expect(
      find.textContaining('sans').evaluate().isNotEmpty ||
      find.textContaining('without').evaluate().isNotEmpty,
      isTrue,
    );
  });

  testWidgets('shows lock icon in privacy footnote', (tester) async {
    await tester.pumpWidget(_makeApp(
      db: db, apiClient: mockApi, consentService: consentService,
    ));
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.lock_outline), findsOneWidget);
  });

  testWidgets('shows three data point emojis', (tester) async {
    await tester.pumpWidget(_makeApp(
      db: db, apiClient: mockApi, consentService: consentService,
    ));
    await tester.pumpAndSettle();
    expect(find.textContaining('📊'), findsOneWidget);
    expect(find.textContaining('🍽️'), findsOneWidget);
    expect(find.textContaining('😴'), findsOneWidget);
  });

  // ── Decline flow ─────────────────────────────────────────────────────────────

  testWidgets('tapping decline marks service declined', (tester) async {
    await tester.pumpWidget(_makeApp(
      db: db, apiClient: mockApi, consentService: consentService,
    ));
    await tester.pumpAndSettle();

    // The screen is taller than the 800×600 test viewport — scroll to buttons.
    final declineBtn = find.textContaining('sans').first;
    await tester.ensureVisible(declineBtn);
    await tester.pumpAndSettle();
    await tester.tap(declineBtn, warnIfMissed: false);
    await tester.pump();

    expect(consentService.hasDeclinedLocally, isTrue);
  });

  // ── Accept flow ──────────────────────────────────────────────────────────────

  testWidgets('accept button calls giveConsent on ApiClient', (tester) async {
    await tester.pumpWidget(_makeApp(
      db: db, apiClient: mockApi, consentService: consentService,
    ));
    await tester.pumpAndSettle();

    final acceptBtn = find.textContaining('Accepter').first;
    await tester.ensureVisible(acceptBtn);
    await tester.pumpAndSettle();
    await tester.tap(acceptBtn, warnIfMissed: false);
    await tester.pump();

    verify(() => mockApi.giveConsent()).called(1);
  });

  testWidgets('loading indicator shown while accepting', (tester) async {
    // Use a Completer so the future never resolves during the test
    // (avoids the pending-timer assertion from Future.delayed).
    final completer = Completer<bool>();
    when(() => mockApi.giveConsent()).thenAnswer((_) => completer.future);

    await tester.pumpWidget(_makeApp(
      db: db, apiClient: mockApi, consentService: consentService,
    ));
    await tester.pumpAndSettle();

    final acceptBtn = find.textContaining('Accepter').first;
    await tester.ensureVisible(acceptBtn);
    await tester.pumpAndSettle();
    await tester.tap(acceptBtn, warnIfMissed: false);
    await tester.pump(); // trigger setState(_isLoading = true)

    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    // Complete the future cleanly so no pending work remains at teardown.
    completer.complete(true);
    await tester.pumpAndSettle();
  });
}
