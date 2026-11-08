import 'package:amina/features/notifications/d2_live_notifications_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/d2_notification_gateway.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

class _FakeGateway implements D2NotificationGateway {
  bool enabled = false;
  int read = 0;
  int deleted = 0;

  D2InboxState get snapshot => D2InboxState(
    proactivityEnabled: enabled,
    locale: 'fr',
    noticeVersion: 'd2.inapp.proactivity.2026-11-08.v1',
    noticeDigest: List.filled(64, 'a').join(),
    noticeText: 'Synthetic explicit consent, never patient data.',
    items: deleted > 0 ? const [] : [
      D2NoticeItem(
        id: 8,
        kind: 'event',
        code: 'ai_consent_given',
        createdAt: DateTime.utc(2026, 11, 8),
        expiresAt: DateTime.utc(2026, 11, 15),
        readAt: read > 0 ? DateTime.utc(2026, 11, 8, 18) : null,
      ),
    ],
  );

  @override
  Future<D2InboxState> inbox(String locale) async => snapshot;

  @override
  Future<D2InboxState> enable(D2InboxState accepted) async {
    enabled = true;
    return snapshot;
  }

  @override
  Future<D2InboxState> disable(String locale) async {
    enabled = false;
    return snapshot;
  }

  @override
  Future<D2InboxState> readOne(int id, String locale) async {
    read++;
    return snapshot;
  }

  @override
  Future<D2InboxState> readAll(String locale) async {
    read++;
    return snapshot;
  }

  @override
  Future<D2InboxState> deleteOne(int id, String locale) async {
    deleted++;
    return snapshot;
  }
}

void main() {
  for (final locale in const ['fr', 'ar', 'en']) {
    testWidgets('D2 in-app live UI: factual items and revocable consent $locale',
        (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      final fake = _FakeGateway();
      final router = GoRouter(
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) =>
                D2LiveNotificationsScreen(gateway: fake),
          ),
          GoRoute(
            path: '/dashboard',
            builder: (context, state) => const Scaffold(body: Text('HOME')),
          ),
        ],
      );
      addTearDown(() async {
        router.dispose();
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });
      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: router,
          locale: Locale(locale),
          supportedLocales: AppLocalizations.supportedLocales,
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('d2-live-notifications-screen')),
          findsOneWidget);
      expect(find.byKey(const ValueKey('d2-notice-8')), findsOneWidget);
      expect(find.byKey(const ValueKey('d2-read-all')), findsOneWidget);
      expect(find.text('D3_REMINDERS_DESTINATION'), findsNothing);
      expect(tester.takeException(), isNull);

      await tester.tap(find.byKey(const ValueKey('d2-read-all')));
      await tester.pumpAndSettle();
      expect(fake.read, 1);
      expect(find.byKey(const ValueKey('d2-read-all')), findsNothing);

      await tester.ensureVisible(
        find.byKey(const ValueKey('d2-proactivity-toggle')),
      );
      await tester.tap(find.byKey(const ValueKey('d2-proactivity-toggle')));
      await tester.pumpAndSettle();
      expect(fake.enabled, isFalse); // explicit confirmation required
      final confirmation = switch (locale) {
        'ar' => 'تفعيل',
        'en' => 'Enable',
        _ => 'Activer',
      };
      await tester.tap(find.text(confirmation));
      await tester.pumpAndSettle();
      expect(fake.enabled, isTrue);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('D2 fail-closed: gateway outage displays no invented notice',
      (tester) async {
    final fake = _ThrowingGateway();
    await tester.pumpWidget(
      MaterialApp(home: D2LiveNotificationsScreen(gateway: fake)),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('d2-live-unavailable')), findsOneWidget);
    expect(find.byKey(const ValueKey('d2-notice-8')), findsNothing);
    expect(find.byKey(const ValueKey('d2-proactivity-toggle')), findsNothing);
  });
}

class _ThrowingGateway extends _FakeGateway {
  @override
  Future<D2InboxState> inbox(String locale) async {
    throw StateError('Synthetic backend outage');
  }
}
