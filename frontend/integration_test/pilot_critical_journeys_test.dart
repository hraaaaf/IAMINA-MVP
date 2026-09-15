import 'package:amina/data/drift/database.dart';
import 'package:amina/features/auth/login_screen.dart';
import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:provider/provider.dart';

class _FailingAuthService extends AuthService {
  @override
  Future<void> signInWithEmail(String email, String password) async {
    throw StateError('synthetic authentication failure');
  }
}

class _FailingCompanionService extends CompanionService {
  @override
  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) async {
    throw const ProviderApiException(
      code: 'provider_timeout',
      message: 'The AI service did not respond in time.',
      retryable: true,
      statusCode: 503,
    );
  }

  @override
  void dispose() {}
}

Widget _localizedApp(Widget home) {
  return MaterialApp(
    locale: const Locale('fr'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: home,
  );
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('auth entry fails safely without leaving login', (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    final auth = _FailingAuthService();
    final api = ApiClient(authService: auth);
    addTearDown(() async {
      auth.dispose();
      await db.close();
    });

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<AuthService>.value(value: auth),
          Provider<AppDatabase>.value(value: db),
          Provider<ApiClient>.value(value: api),
        ],
        child: _localizedApp(const LoginScreen()),
      ),
    );
    await tester.pumpAndSettle();

    final fields = find.byType(TextField);
    expect(fields, findsNWidgets(2));
    await tester.enterText(fields.at(0), 'pilot@example.test');
    await tester.enterText(fields.at(1), 'wrong-password');

    final loginContext = tester.element(find.byType(LoginScreen));
    final l10n = AppLocalizations.of(loginContext)!;
    await tester.tap(find.text(l10n.signIn).first);
    await tester.pumpAndSettle();

    expect(find.byType(LoginScreen), findsOneWidget);
    expect(find.text(l10n.loginError), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('glucose logging persists to an isolated local database', (
    tester,
  ) async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(() async => db.close());

    await tester.pumpWidget(
      _localizedApp(
        MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            Provider<PatientProfileData?>.value(value: null),
          ],
          child: const Scaffold(body: AddLogSheet()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('glucose-input')),
      '123',
    );
    await tester.tap(find.byKey(const Key('save-log-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
    final persisted = await db.select(db.logEntries).get();
    expect(persisted, hasLength(1));
    expect(persisted.single.bloodSugar, 123);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Companion provider timeout is surfaced as typed safe UX', (
    tester,
  ) async {
    await tester.pumpWidget(
      _localizedApp(
        CompanionConversationScreen(service: _FailingCompanionService()),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('companion-chat-input')),
      'Bonjour',
    );
    await tester.tap(find.byKey(const Key('companion-chat-send')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('companion-chat-failure')), findsOneWidget);
    expect(
      find.text(
        'IAmina met trop de temps à répondre. Réessaie dans un instant.',
      ),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
}
