// ConsentScreen — widget tests
//
// Verifies the versioned consent gate renders correctly and responds to user actions.
import 'dart:async';
import 'dart:convert';

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
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

final class _TestApiClient extends ApiClient {
  _TestApiClient(this._testClient) : super(baseUrl: 'http://localhost:8000');

  final ChopperClient _testClient;

  @override
  ChopperClient get client => _testClient;
}

class _FakeConsentEvidenceStore extends ConsentEvidenceStore {
  ConsentNoticeClaim? written;

  @override
  Future<ConsentNoticeClaim?> readCurrent() async => written;

  @override
  Future<bool> hasCurrentEvidence() async => written != null;

  @override
  Future<void> write(ConsentNoticeClaim claim) async {
    written = claim;
  }

  @override
  Future<void> clear() async {
    written = null;
  }
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
  late ChopperClient chopper;
  late _TestApiClient apiClient;
  late ConsentService consentService;
  late _FakeConsentEvidenceStore evidenceStore;
  late ConsentNoticeClaim claim;
  late http.Request? capturedRequest;
  late bool responseSuccess;
  Completer<http.Response>? responseCompleter;

  http.Response successResponse() => http.Response(
    jsonEncode({
      'ai_consent_given': true,
      'notice_version': claim.version,
      'notice_hash': claim.noticeHash,
      'locale': claim.locale,
    }),
    200,
    headers: const {'content-type': 'application/json'},
  );

  setUp(() {
    db = _openDb();
    claim = ConsentNoticeContract.forLocale('fr');
    capturedRequest = null;
    responseSuccess = true;
    responseCompleter = null;
    consentService = ConsentService();
    evidenceStore = _FakeConsentEvidenceStore();

    chopper = ChopperClient(
      baseUrl: Uri.parse('http://localhost:8000'),
      client: MockClient((request) async {
        capturedRequest = request;
        final pending = responseCompleter;
        if (pending != null) return pending.future;
        if (!responseSuccess) {
          return http.Response(
            jsonEncode({'detail': 'rejected'}),
            422,
            headers: const {'content-type': 'application/json'},
          );
        }
        return successResponse();
      }),
      converter: const JsonConverter(),
    );
    apiClient = _TestApiClient(chopper);
  });

  tearDown(() async {
    consentService.dispose();
    chopper.dispose();
    await db.close();
  });

  Widget app() => _makeApp(
    db: db,
    apiClient: apiClient,
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

    expect(capturedRequest, isNotNull);
    expect(capturedRequest!.method, 'POST');
    expect(capturedRequest!.url.path, '/api/v1/account/consent');
    expect(
      jsonDecode(capturedRequest!.body),
      {
        'notice_version': claim.version,
        'notice_hash': claim.noticeHash,
        'locale': claim.locale,
      },
    );
    expect(evidenceStore.written?.version, claim.version);
    expect(evidenceStore.written?.noticeHash, claim.noticeHash);
    expect(evidenceStore.written?.locale, claim.locale);
    expect(consentService.hasConsent, isTrue);
    expect(find.text('Dashboard'), findsOneWidget);
  });

  testWidgets('loading indicator shown while accepting', (tester) async {
    final completer = Completer<http.Response>();
    responseCompleter = completer;

    await tester.pumpWidget(app());
    await tester.pumpAndSettle();

    final acceptBtn = find.text('Accepter et continuer');
    await tester.ensureVisible(acceptBtn);
    await tester.tap(acceptBtn);
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    completer.complete(successResponse());
    await tester.pumpAndSettle();
    expect(find.byType(CircularProgressIndicator), findsNothing);
  });

  testWidgets('failed consent response stays fail-closed', (tester) async {
    responseSuccess = false;

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
