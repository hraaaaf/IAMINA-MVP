import 'dart:async';
import 'package:amina/features/notifications/d2_notification_center_screen.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:amina/services/d2_consent_gateway.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

// Synthetic Web FUE. Never connects to a patient, server or push provider.
class _FUEGateway implements D2ConsentGateway {
  bool consent = false, offline = false;
  int grants = 0, revokes = 0, previews = 0, inboxReads = 0;
  int saves = 0, reads = 0, deletes = 0;
  List<D2SavedNotice> items = const [];
  D2ObservationPreview? eligible;
  Completer<D2ConsentStatus>? pending;

  D2ConsentStatus status(String locale) => D2ConsentStatus(
    optedIn: consent,
    noticeText: locale.startsWith('ar')
        ? 'معاينة اختيارية فقط. لا رسائل تلقائية ولا إشعارات.'
        : 'Aperçu facultatif uniquement. Aucun envoi automatique.',
    noticeVersion: '2026-10-20.d2.1',
    noticeHash: 'a' * 64,
    locale: locale.startsWith('ar') ? 'ar' : 'fr',
  );
  @override
  Future<D2ConsentStatus> read(String locale) async {
    if (offline) throw StateError('offline fixture');
    return pending == null ? status(locale) : pending!.future;
  }
  @override
  Future<D2ConsentStatus> grant(D2ConsentStatus acceptedNotice) async {
    grants++; consent = true;
    return status(acceptedNotice.locale);
  }
  @override
  Future<D2ConsentStatus> withdraw(String locale) async {
    revokes++; consent = false; items = const [];
    return status(locale);
  }
  @override
  Future<D2ObservationPreview?> readPreview() async { previews++; return eligible; }
  @override
  Future<List<D2SavedNotice>> inbox() async { inboxReads++; return items; }
  @override
  Future<List<D2SavedNotice>> savePreview() async {
    saves++; items = [const D2SavedNotice(id: 1, kind: 'meal')]; return items;
  }
  @override
  Future<List<D2SavedNotice>> markRead(int id) async {
    reads++; items = [D2SavedNotice(id: id, kind: 'meal', read: true)];
    return items;
  }
  @override
  Future<List<D2SavedNotice>> removeNotice(int id) async {
    deletes++; items = const []; return items;
  }
}

Widget _app(_FUEGateway gateway, String language) => MaterialApp(
  locale: Locale(language),
  supportedLocales: const [Locale('fr'), Locale('ar')],
  localizationsDelegates: const [
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  home: D2NotificationCenterScreen(gateway: gateway),
);

Future<void> _size(WidgetTester tester, double width, double height) async {
  tester.view.devicePixelRatio = 1;
  await tester.binding.setSurfaceSize(Size(width, height));
  addTearDown(() async {
    await tester.binding.setSurfaceSize(null);
    tester.view.resetDevicePixelRatio();
  });
}

Future<void> _tap(WidgetTester tester, Finder target) async {
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  await tester.tap(target);
  await tester.pumpAndSettle();
}

void main() {
  for (final language in ['fr', 'ar']) {
    for (final dimensions in [
      (390.0, 844.0), (768.0, 1024.0), (1280.0, 900.0)
    ]) {
      final (width, height) = dimensions;
      testWidgets('D2 Web FUE ' + language + ' ' +
          width.toInt().toString() + 'x' + height.toInt().toString() +
          ': OFF, consent, revoke', (tester) async {
        await _size(tester, width, height);
        final g = _FUEGateway();
        await tester.pumpWidget(_app(g, language));
        await tester.pumpAndSettle();
        expect(Directionality.of(tester.element(
          find.byType(D2NotificationCenterScreen))),
          language == 'ar' ? TextDirection.rtl : TextDirection.ltr);
        expect(find.byKey(const Key('d2-inbox-title')), findsOneWidget);
        expect(find.byKey(const Key('d2-server-notice')), findsOneWidget);
        expect(find.byKey(const Key('d2-governed-preview')), findsNothing);
        expect(g.previews, 0);
        expect(g.inboxReads, 0);
        expect(g.saves, 0);
        expect(tester.widget<FilledButton>(
          find.byKey(const Key('d2-enable-preview-only'))).onPressed, isNull);
        expect(tester.takeException(), isNull);

        await _tap(tester, find.byKey(const Key('d2-acknowledge-notice')));
        expect(tester.widget<FilledButton>(
          find.byKey(const Key('d2-enable-preview-only'))).onPressed,
          isNotNull);
        await _tap(tester, find.byKey(const Key('d2-enable-preview-only')));
        expect(g.grants, 1);
        expect(g.consent, isTrue);
        expect(g.previews, 1);
        expect(g.inboxReads, 1);
        expect(find.byKey(const Key('d2-empty-inbox')), findsOneWidget);
        expect(find.byKey(const Key('d2-withdraw-consent')), findsOneWidget);
        expect(tester.takeException(), isNull);

        await _tap(tester, find.byKey(const Key('d2-withdraw-consent')));
        expect(g.revokes, 1);
        expect(g.consent, isFalse);
        expect(g.items, isEmpty);
        expect(tester.widget<FilledButton>(
          find.byKey(const Key('d2-enable-preview-only'))).onPressed, isNull);
        expect(tester.takeException(), isNull);
      });
    }

    testWidgets('D2 Web FUE ' + language + ': offline and Retry',
      (tester) async {
        await _size(tester, 390, 844);
        final g = _FUEGateway()..offline = true;
        await tester.pumpWidget(_app(g, language));
        await tester.pumpAndSettle();
        expect(find.byKey(const Key('d2-error')), findsOneWidget);
        expect(find.byKey(const Key('d2-enable-preview-only')), findsNothing);
        expect(g.grants, 0);
        expect(g.previews, 0);
        g.offline = false;
        await _tap(tester, find.text(
          language == 'ar' ? 'إعادة المحاولة' : 'Réessayer'));
        expect(find.byKey(const Key('d2-error')), findsNothing);
        expect(find.byKey(const Key('d2-enable-preview-only')), findsOneWidget);
        expect(g.consent, isFalse);
        expect(g.grants, 0);
        expect(tester.takeException(), isNull);
      });
  }

  testWidgets('D2 Web FUE FR: voluntary save, read, delete', (tester) async {
    await _size(tester, 390, 844);
    final g = _FUEGateway()
      ..consent = true
      ..eligible = const D2ObservationPreview(
        kind: 'meal', state: 'monitoring', allowedNextStep: 'MONITOR');
    await tester.pumpWidget(_app(g, 'fr'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('d2-governed-preview')), findsOneWidget);
    expect(g.saves, 0);
    await _tap(tester, find.byKey(const Key('d2-save-preview')));
    expect(g.saves, 1);
    expect(find.byKey(const Key('d2-inbox-item-1')), findsOneWidget);
    await _tap(tester, find.byTooltip('Marquer comme lu'));
    expect(g.reads, 1);
    await _tap(tester, find.byTooltip('Supprimer'));
    expect(g.deletes, 1);
    expect(g.items, isEmpty);
    expect(find.byKey(const Key('d2-empty-inbox')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('D2 Web FUE: A to B race does not expose stale A consent',
    (tester) async {
      final g = _FUEGateway()..pending = Completer<D2ConsentStatus>();
      await tester.pumpWidget(_app(g, 'fr'));
      await tester.pump();
      expect(find.byKey(const Key('d2-enable-preview-only')), findsNothing);
      AuthEpoch.advance();
      // Simulate A's late response saying consent is ON, after session B starts.
      g.consent = true;
      g.pending!.complete(g.status('fr'));
      // A loading spinner deliberately remains active when stale data is
      // discarded. pumpAndSettle() would time out: inspect one settled frame,
      // not the completion of an intentionally nonsettling spinner.
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      expect(find.byKey(const Key('d2-enable-preview-only')), findsNothing);
      expect(find.byKey(const Key('d2-withdraw-consent')), findsNothing);
      expect(find.byKey(const Key('d2-server-notice')), findsNothing);
      expect(find.byKey(const Key('d2-governed-preview')), findsNothing);
      expect(g.previews, 0);
      expect(g.inboxReads, 0);
      expect(g.grants, 0);
      expect(tester.takeException(), isNull);
    });
}
