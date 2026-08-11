import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:provider/provider.dart';
import 'package:amina/features/journal/widgets/amina_chat_view.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/services/api_client.dart';
import '../../mocks.dart';

// ── Platform channel mocks ────────────────────────────────────────────────────
// flutter_tts and record use MethodChannels that aren't available in tests.
// We install no-op handlers so the widget initialises without errors.

void _mockPlatformChannels() {
  const ttsChannel = MethodChannel('flutter_tts');
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(ttsChannel, (call) async {
        if (call.method == 'getLanguages') return <dynamic>['fr-FR', 'ar'];
        return null;
      });

  const recordChannel = MethodChannel('com.llfbandit.record/messages');
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(recordChannel, (_) async => null);
}

// ── In-memory database ────────────────────────────────────────────────────────

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

// ── Pump helper ───────────────────────────────────────────────────────────────
// AminaChatView contains a repeating AnimationController (_pulseCtrl) that
// never settles, so pumpAndSettle() always times out.  Use this helper instead:
// first pump lets initState run, second pump drains async DB reads.
Future<void> _settle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 300));
}

// ── Widget factory ────────────────────────────────────────────────────────────

Widget _makeChat({
  required AppDatabase db,
  required ApiClient apiClient,
  String? initialMessage,
}) {
  return MaterialApp(
    home: Scaffold(
      body: MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          Provider<ApiClient>.value(value: apiClient),
        ],
        child: AminaChatView(onClose: () {}, initialMessage: initialMessage),
      ),
    ),
  );
}

void main() {
  late AppDatabase db;
  late MockApiClient mockApi;

  setUpAll(() {
    registerFallbackValue('');
    _mockPlatformChannels();
  });

  setUp(() {
    db = _openDb();
    mockApi = MockApiClient();
    // Default: chatStream returns empty stream
    when(
      () => mockApi.chatStream(any()),
    ).thenAnswer((_) => const Stream.empty());
  });

  tearDown(() async {
    await db.close();
  });

  // ── Initial render ───────────────────────────────────────────────────────────

  testWidgets('renders without error (smoke test)', (tester) async {
    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    expect(find.byType(AminaChatView), findsOneWidget);
  });

  testWidgets('shows "IAmina" in header', (tester) async {
    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    expect(find.text('IAmina'), findsOneWidget);
  });

  testWidgets('shows chat input placeholder', (tester) async {
    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    expect(find.text('Posez une question à IAmina…'), findsOneWidget);
  });

  testWidgets('shows welcome message when history is empty', (tester) async {
    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    expect(find.textContaining('Bonjour'), findsOneWidget);
  });

  testWidgets('shows suggested prompts when no user message sent', (
    tester,
  ) async {
    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    // At least one of the fallback suggestions should be visible
    expect(
      find
              .textContaining('Comment se passe ma semaine')
              .evaluate()
              .isNotEmpty ||
          find.textContaining('hypos').evaluate().isNotEmpty ||
          find.textContaining('Éviter').evaluate().isNotEmpty,
      isTrue,
    );
  });

  testWidgets('close button is present and tappable', (tester) async {
    bool closed = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MultiProvider(
            providers: [
              Provider<AppDatabase>.value(value: db),
              Provider<ApiClient>.value(value: mockApi),
            ],
            child: AminaChatView(onClose: () => closed = true),
          ),
        ),
      ),
    );
    await _settle(tester);

    await tester.tap(find.byIcon(Icons.close));
    await tester.pump();

    expect(closed, isTrue);
  });

  testWidgets('send button is visible', (tester) async {
    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    expect(find.byIcon(Icons.send_rounded), findsOneWidget);
  });

  testWidgets('mic button is visible', (tester) async {
    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    expect(find.byIcon(Icons.mic_rounded), findsOneWidget);
  });

  // ── Sending a message ────────────────────────────────────────────────────────

  testWidgets('typing a message and sending adds user bubble', (tester) async {
    when(
      () => mockApi.chatStream(any()),
    ).thenAnswer((_) => Stream.fromIterable(['Voici ma réponse.']));

    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    // Type a message
    await tester.enterText(find.byType(TextField), 'Comment va ma glycémie ?');
    await tester.pump();

    // Submit
    await tester.tap(find.byIcon(Icons.send_rounded));
    await tester.pump();

    // User bubble is visible
    expect(find.text('Comment va ma glycémie ?'), findsOneWidget);
  });

  testWidgets('suggested prompts disappear after first user message', (
    tester,
  ) async {
    when(
      () => mockApi.chatStream(any()),
    ).thenAnswer((_) => Stream.fromIterable(['OK']));

    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    // At least ONE suggestion chip is visible before any user message.
    // (The exact set depends on IAmina's welcome message — any chip qualifies.)
    final promptsBefore =
        find
            .textContaining('Comment se passe ma semaine')
            .evaluate()
            .isNotEmpty ||
        find.textContaining('Éviter').evaluate().isNotEmpty ||
        find.textContaining('Pourquoi ce pic').evaluate().isNotEmpty ||
        find.textContaining('Mon meilleur').evaluate().isNotEmpty ||
        find.textContaining('hypos').evaluate().isNotEmpty;
    expect(promptsBefore, isTrue);

    // Send a message
    await tester.enterText(find.byType(TextField), 'Bonjour');
    await tester.tap(find.byIcon(Icons.send_rounded));
    await tester.pump();

    // ALL suggestion chips must be gone after a user message is sent
    expect(find.textContaining('Comment se passe ma semaine'), findsNothing);
    expect(find.textContaining('Pourquoi ce pic'), findsNothing);
    expect(find.textContaining('Mon meilleur'), findsNothing);
  });

  // ── History loading ──────────────────────────────────────────────────────────

  testWidgets('loads and shows existing chat history from DB', (tester) async {
    // Seed the DB with a prior conversation
    await db
        .into(db.chatMessages)
        .insert(
          ChatMessagesCompanion.insert(
            conversationId: 'default',
            role: 'assistant',
            message: 'Salut, je suis IAmina !',
            createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
          ),
        );
    await db
        .into(db.chatMessages)
        .insert(
          ChatMessagesCompanion.insert(
            conversationId: 'default',
            role: 'user',
            message: 'Mon TIR ?',
            createdAt: DateTime.now().subtract(const Duration(minutes: 4)),
          ),
        );

    await tester.pumpWidget(_makeChat(db: db, apiClient: mockApi));
    await _settle(tester);

    expect(find.text('Salut, je suis IAmina !'), findsOneWidget);
    expect(find.text('Mon TIR ?'), findsOneWidget);
  });

  testWidgets('initialMessage pre-fills text field', (tester) async {
    await tester.pumpWidget(
      _makeChat(
        db: db,
        apiClient: mockApi,
        initialMessage: 'Mon pic glycémique',
      ),
    );
    await _settle(tester);

    final tf = tester.widget<TextField>(find.byType(TextField));
    expect(tf.controller?.text, 'Mon pic glycémique');
  });
}
