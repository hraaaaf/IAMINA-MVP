import 'package:amina/data/drift/database.dart';
import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class _Authenticated extends AuthService {
  @override
  bool get isAuditSession => false;
}

class _GovernedFallback extends CompanionService {
  @override
  Future<CompanionChatReply?> sendChatMessage(
    String message, {
    int contextDays = 14,
  }) async {
    return const CompanionChatReply(
      reply: 'Réponse locale limitée.',
      conversationId: 'conv-test',
      replyLanguage: 'fr',
      responseMode: 'governance_fallback',
    );
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
            const MethodChannel('flutter_tts'), (_) async => null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
            const MethodChannel('com.llfbandit.record/messages'),
            (_) async => null);
  });

  for (final language in ['fr', 'en', 'ar']) {
    for (final size in const [Size(390, 844), Size(360, 560)]) {
      for (final scale in const [1.0, 1.6]) {
        testWidgets(
          'empty chat suggests a question without submitting '
          '$language at ${size.width.toInt()}x${size.height.toInt()} text x$scale',
          (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        final db = AppDatabase(NativeDatabase.memory());
        addTearDown(db.close);

        await tester.pumpWidget(MultiProvider(
          providers: [
            Provider<AppDatabase>.value(value: db),
            Provider<AuthService>(create: (_) => _Authenticated()),
          ],
          child: MaterialApp(
            locale: Locale(language),
            supportedLocales: [Locale(language)],
            localizationsDelegates: const [
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            home: Builder(
              builder: (context) => MediaQuery(
                data: MediaQuery.of(context).copyWith(
                  textScaler: TextScaler.linear(scale),
                ),
                child: CompanionConversationScreen(
                  service: _GovernedFallback(),
                ),
              ),
            ),
          ),
        ));
        await tester.pump();
        final suggestion =
            find.byKey(const Key('companion-chat-suggestion-reading'));
        expect(suggestion, findsOneWidget);
        expect(
          find.byKey(const Key('companion-chat-suggestion-capabilities')),
          findsOneWidget,
        );
        await tester.ensureVisible(suggestion);
        await tester.tap(suggestion);
        await tester.pump();
        final input = tester.widget<TextField>(
          find.byKey(const Key('companion-chat-input')),
        );
        expect(input.controller!.text, isNotEmpty);
        expect(
          find.byKey(const Key('companion-chat-message-list')),
          findsNothing,
        );
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox.shrink());
        });
      }
    }
  }

  testWidgets('first reading stays local and denied AI mode is explicit',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    await db.into(db.logEntries).insert(LogEntriesCompanion.insert(
      createdAt: DateTime.now(),
      bloodSugar: 128,
      clientUuid: 'synthetic-reading-1',
      loggedAt: Value(DateTime.now()),
    ));

    expect((await db.getRecentLogs(limit: 1)).single.bloodSugar, 128);

    await tester.pumpWidget(MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: db),
          Provider<AuthService>(create: (_) => _Authenticated()),
        ],
        child: MaterialApp(
          locale: const Locale('fr'),
          supportedLocales: const [Locale('fr')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: CompanionConversationScreen(
            service: _GovernedFallback(),
            latestLocalReading: () async =>
                (await db.getRecentLogs(limit: 1)).first.bloodSugar,
          ),
        ),
    ));
    await tester.pump();
    await tester.enterText(
      find.byKey(const Key('companion-chat-input')),
      'Que peux-tu me dire de ma première mesure ?',
    );
    await tester.tap(find.byKey(const Key('companion-chat-send')));
    await tester.pump();
    // Drift's native executor may complete asynchronously outside fake time.
    await tester.runAsync(() async {
      await Future<void>.delayed(const Duration(milliseconds: 400));
    });
    await tester.pumpAndSettle();
    final present = tester.widgetList<Text>(find.byType(Text))
        .map((text) => text.data)
        .whereType<String>()
        .toList(growable: false);
    debugPrint('P1 synthetic widget texts: $present');

    expect(find.textContaining('128 mg/dL'), findsOneWidget);
    expect(find.textContaining('n’est pas vérifiée'), findsOneWidget);
    expect(find.byKey(const Key('companion-governance-fallback-label')),
        findsOneWidget);
    expect(find.text('Réponse locale limitée.'), findsOneWidget);


  });

  for (final synced in [false, true]) {
    testWidgets('production path reads Drift ${synced ? 'synced' : 'pending'}',
        (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    final rowId = await db.into(db.logEntries).insert(LogEntriesCompanion.insert(
      createdAt: DateTime.now(),
      bloodSugar: 128,
      clientUuid: 'synthetic-reading-2',
      loggedAt: Value(DateTime.now()),
    ));
    if (synced) await db.markLogAsSynced(rowId);
    final recorded = (await db.getRecentLogs(limit: 1)).single;
    expect(recorded.bloodSugar, 128);
    expect(recorded.syncStatus, synced ? 'synced' : 'pending');

    await tester.pumpWidget(MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        Provider<AuthService>(create: (_) => _Authenticated()),
      ],
      child: MaterialApp(
        locale: const Locale('fr'),
        supportedLocales: const [Locale('fr')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: CompanionConversationScreen(service: _GovernedFallback()),
      ),
    ));
    await tester.enterText(
      find.byKey(const Key('companion-chat-input')),
      'Que peux-tu me dire de ma première mesure ?',
    );
    await tester.tap(find.byKey(const Key('companion-chat-send')));
    await tester.runAsync(() async {
      await Future<void>.delayed(const Duration(milliseconds: 400));
    });
    await tester.pumpAndSettle();
    expect(find.textContaining('128 mg/dL'), findsOneWidget);
    expect(
      find.textContaining(
        synced ? 'marquée comme synchronisée' : 'en attente de synchronisation',
      ),
      findsOneWidget,
    );
    expect(find.byKey(const Key('companion-governance-fallback-label')),
        findsOneWidget);
  });
  }

  testWidgets('empty device states absence without inventing server history',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    await tester.pumpWidget(MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        Provider<AuthService>(create: (_) => _Authenticated()),
      ],
      child: MaterialApp(
        locale: const Locale('fr'),
        supportedLocales: const [Locale('fr')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: CompanionConversationScreen(
          service: _GovernedFallback(),
          latestLocalReading: () async => null,
        ),
      ),
    ));
    await tester.pump();
    await tester.enterText(
      find.byKey(const Key('companion-chat-input')),
      'Que peux-tu me dire de ma première mesure ?',
    );
    await tester.tap(find.byKey(const Key('companion-chat-send')));
    await tester.pump();
    await tester.runAsync(() async {
      await Future<void>.delayed(const Duration(milliseconds: 400));
    });
    await tester.pumpAndSettle();

    expect(find.textContaining('Aucune mesure de glycémie'), findsOneWidget);
    expect(find.textContaining('serveur'), findsOneWidget);
    expect(
      find.byKey(const Key('companion-governance-fallback-label')),
      findsOneWidget,
    );
  });
}
