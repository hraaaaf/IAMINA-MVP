import 'dart:io';
import 'dart:ui' as ui;

import 'package:amina/data/drift/database.dart';
import 'package:amina/features/companion/companion_conversation_screen.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/companion_service.dart';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter/rendering.dart';
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

    await tester.pumpWidget(RepaintBoundary(
      key: const Key('p1-chat-proof-root'),
      child: MultiProvider(
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

    // A real 390×844 rasterization of the revised Flutter widget, no prod deploy.
    final boundary = tester.renderObject(
      find.byKey(const Key('p1-chat-proof-root')),
    ) as RenderRepaintBoundary;
    final image = await boundary.toImage(pixelRatio: 1);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    expect(bytes, isNotNull);
    final directory = Directory('test-artifacts');
    directory.createSync(recursive: true);
    File('test-artifacts/p1-chat-after-390x844.png')
        .writeAsBytesSync(bytes!.buffer.asUint8List());
    image.dispose();
  });

  testWidgets('production provider path reads Drift without injection',
      (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    await db.into(db.logEntries).insert(LogEntriesCompanion.insert(
      createdAt: DateTime.now(),
      bloodSugar: 128,
      clientUuid: 'synthetic-reading-2',
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
  });
}
