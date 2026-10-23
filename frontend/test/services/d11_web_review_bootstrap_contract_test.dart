import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D11 hosted Vercel waits for old PWA cleanup before Flutter load', () {
    final source = File('web/flutter_bootstrap.js').readAsStringSync();

    final hostedStart = source.indexOf('async function startHostedReview()');
    final cleanup = source.indexOf(
      'await cleanupHostedReviewCaches();',
      hostedStart,
    );
    final boot = source.indexOf('_flutter.loader.load();', cleanup);
    final hostedDispatch = source.indexOf(
      'if (IAMINA_HOSTED_REVIEW) {\n  startHostedReview()',
    );

    expect(hostedStart, greaterThan(0));
    expect(cleanup, greaterThan(hostedStart));
    expect(boot, greaterThan(cleanup));
    expect(hostedDispatch, greaterThan(boot));
    expect(
      source.substring(0, hostedStart),
      isNot(contains('_flutter.loader.load();')),
      reason: 'A top-level Flutter load reintroduces the stale-SW race',
    );
  });

  test('D11 review recovery has a once-only reload and keeps patient vaults', () {
    final source = File('web/flutter_bootstrap.js').readAsStringSync();
    expect(source, contains('navigator.serviceWorker?.controller'));
    expect(source, contains("!== 'attempted'"));
    expect(source, contains("sessionStorage.setItem("));
    expect(source, contains('window.location.reload();'));
    expect(source, contains('sessionStorage.removeItem('));
    expect(source, contains("name.startsWith('iamina-app-shell-')"));
    expect(source, isNot(contains('indexedDB.deleteDatabase')));
    expect(source, isNot(contains('localStorage.clear()')));
  });
}
