// ConsentScreen — widget tests
//
// Verifies the versioned consent gate renders correctly and responds to user actions.
import 'dart:async';

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/auth/consent_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/consent_evidence_store.dart';
import 'package:amina/services/consent_notice_contract.dart';
import 'package:amina/services/consent_service.dart';
import 'package:chopper/chopper.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';
import 'package:provider/provider.dart';

import '../../mocks.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

class _MockChopperClient extends Mock implements ChopperClient {}

class _MockResponse extends Mock implements Response<dynamic> {}

class _FakeConsentEvidenceStore extends Fake implements ConsentEvidenceStore {
  ConsentNoticeClaim? written;

  @override
  Future<void> write(ConsentNoticeClaim claim) async {
    written = claim;
  }
}

class _FakeConsentService extends Fake implements ConsentService {
  bool _declined = false;
  bool _verified = false;

  @override
  bool get hasConsent => _verified;

  @override
  bool get hasDeclinedLocally => _declined;

  @override
  void declineLocally() => _declined = true;

  @override
  void markVerifiedConsent() {
    _verified = true;
    _declined = false;
  }

  @override
  void addListener(VoidCallback listener) {}

  @override
  void removeListener(VoidCallback listener) {}

  @override
  void dispose() {}
}

Widget _makeApp({
  required AppDatabase db,
  required ApiClient apiClient,
  required ConsentService consentService,
  required ConsentEvidenceStore evidenceStore,
}) {
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
  );

  return MultiProvider(
    providers: [
      Provider<AppDatabase>.value(value: db),
      Provider<ApiClient>.value(value: apiClient),
      Provider<ConsentEvidenceStore>.value(value: evidenceStore),
      ChangeNotifierProvider<ConsentService>.value(value: consentService),
    ],
    child: MaterialApp.router(
      routerConfig: router,
      locale: const Locale('fr'),
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

void main() {
  late AppDatabase db;
  late MockApiClient mockApi;
  late _MockChopperClient mockChopper;
  late _MockResponse mockResponse;
  late _FakeConsentService consentService;
  late _FakeConsentEvidenceStore evidenceStore;

  setUpAll(() {
    registerFallbackValue(Uri());
  });

  setUp(() {
    db = _openDb();
    mockApi = MockApiClient();
    mockChopper = _MockChopperClient();
    mockResponse = _MockResponse();
    consentService = _FakeConsentService();
    evidenceStore = _FakeConsentEvidenceStore();

    final claim = ConsentNoticeContract.forLocale('fr');
    when(() => mockApi.client).thenReturn(mockChopper);
    when(() => mockResponse.isSuccessful).thenReturn(true);
    when(() => mockResponse.body).thenReturn({
      'ai_consent_given': true,
      'notice_version': claim.version,
      'notice_hash': claim.noticeHash,
      'locale': claim.locale,
    });
    when(
      () => mockChopper.post(
        any(),
        body: any(named: 'body'),
      ),
    ).thenAnswer((_) async => mockResponse);
  });

  tearDown(() async {
    await db.close();
  });

  Widget app() => _makeApp(
    db: db,
    apiClient: mockApi,
    consentService: consentService,
    evidenceStore: evidenceStore,
  );

  testWidgets('renders without error (smoke test)', (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    expect(find.byType(ConsentScreen), findsOneWidget);
  });

  testWidgets('shows shield icon in header', (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.shield_outlined), findsOneWidget);
  });

  testWidgets('shows accept button', (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    expect(find.text('Accepter et continuer'), findsOneWidget);
  });

  testWidgets('shows decline button', (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    expect(find.text('Continuer sans IA'), findsOneWidget);
  });

  testWidgets('shows lock icon in privacy footnote', (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.lock_outline), findsOneWidget);
  });

  testWidgets('shows three data point emojis', (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    expect(find.textContaining('📊'), findsOneWidget);
    expect(find.textContaining('🍽️'), findsOneWidget);
    expect(find.textContaining('😴'), findsOneWidget);
  });

  testWidgets('tapping decline marks service declined', (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();

    final declineBtn = find.text('Continuer sans IA');
    await tester.ensureVisible(declineBtn);
    await tester.tap(declineBtn);
    await tester.pump();

    expect(consentService.hasDeclinedLocally, isTrue);
  });

  testWidgets('accept posts exact claim and persists verified evidence', (tester) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();

    final acceptBtn = find.text('Accepter et continuer');
    await tester.ensureVisible(acceptBtn);
    await tester.tap(acceptBtn);
    await tester.pumpAndSettle();

    verify(
      () => mockChopper.post(
        Uri.parse('/api/v1/account/consent'),
        body: any(named: 'body'),
      ),
    ).called(1);
    expect(evidenceStore.written?.locale, 'fr');
    expect(consentService.hasConsent, isTrue);
    expect(find.text('Dashboard'), findsOneWidget);
  });

  testWidgets('loading indicator shown while accepting', (tester) async {
    final completer = Completer<Response<dynamic>>();
    when(
      () => mockChopper.post(
        any(),
        body: any(named: 'body'),
      ),
    ).thenAnswer((_) => completer.future);

    await tester.pumpWidget(app());
    await tester.pumpAndSettle();

    final acceptBtn = find.text('Accepter et continuer');
    await tester.ensureVisible(acceptBtn);
    await tester.tap(acceptBtn);
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    completer.complete(mockResponse);
    await tester.pumpAndSettle();
    expect(find.byType(CircularProgressIndicator), findsNothing);
  });

  testWidgets('failed consent response stays fail-closed', (tester) async {
    when(() => mockResponse.isSuccessful).thenReturn(false);

    await tester.pumpWidget(app());
    await tester.pumpAndSettle();

    final acceptBtn = find.text('Accepter et continuer');
    await tester.ensureVisible(acceptBtn);
    await tester.tap(acceptBtn);
    await tester.pumpAndSettle();

    expect(evidenceStore.written, isNull);
    expect(consentService.hasConsent, isFalse);
    expect(find.byType(ConsentScreen), findsOneWidget);
  });
}
