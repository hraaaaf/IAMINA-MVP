/// Temporary W01 synthetic Web Preview diagnostic. No bearer is persisted,
/// displayed, logged, or sent to any origin other than the exact W01 Web BFF.
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

const bool kW01RevocationProbeEnabled = bool.fromEnvironment(
  'IAMINA_W01_SESSION_PROBE',
  defaultValue: false,
);

const String kW01PreviewWebOrigin =
    'https://iamina-review-git-preview-w0-f972e4-achraf-benmoussa-s-projects.vercel.app';

class W01RevocationProbeResult {
  final int? beforeStatus;
  final int? logoutStatus;
  final int? afterStatus;
  final String? failureCode;
  final bool cleanupFailed;

  const W01RevocationProbeResult({
    this.beforeStatus,
    this.logoutStatus,
    this.afterStatus,
    this.failureCode,
    this.cleanupFailed = false,
  });

  bool get passed =>
      beforeStatus == 200 &&
      logoutStatus == 200 &&
      afterStatus == 401 &&
      failureCode == null &&
      !cleanupFailed;

  W01RevocationProbeResult withCleanupFailure() => W01RevocationProbeResult(
    beforeStatus: beforeStatus,
    logoutStatus: logoutStatus,
    afterStatus: afterStatus,
    failureCode: failureCode,
    cleanupFailed: true,
  );
}

// Volatile UI result only; no credentials, clinical values or token material.
final ValueNotifier<W01RevocationProbeResult?> w01RevocationProbeNotice =
    ValueNotifier<W01RevocationProbeResult?>(null);

/// One-click remote proof: active native bearer on /logs must be 200;
/// logout must be 200; exactly the same old bearer on /logs must be 401.
/// This endpoint is GET-only and does not create or modify clinical entries.
/// The caller clears the local credential even when the remote probe fails.
Future<W01RevocationProbeResult> runW01RevocationProbe({
  required String? bearer,
  required String baseUrl,
  http.Client? client,
}) async {
  if (!kW01RevocationProbeEnabled) {
    return const W01RevocationProbeResult(failureCode: 'disabled');
  }
  // No local/demo/Firebase credential may be used for this native proof.
  if (bearer == null || !bearer.startsWith('iamina.')) {
    return const W01RevocationProbeResult(failureCode: 'no_native_bearer');
  }
  final origin = Uri.tryParse(baseUrl);
  if (origin == null ||
      origin.origin != kW01PreviewWebOrigin ||
      origin.path.isNotEmpty ||
      origin.query.isNotEmpty ||
      origin.fragment.isNotEmpty) {
    return const W01RevocationProbeResult(failureCode: 'wrong_preview_origin');
  }

  final ownClient = client == null;
  final httpClient = client ?? http.Client();
  final headers = <String, String>{
    'Authorization': 'Bearer $bearer',
    'Accept': 'application/json',
  };
  Future<http.Response> request(String method, String path) async {
    final req = http.Request(method, origin.resolve(path))
      ..followRedirects = false
      ..headers.addAll(headers);
    final stream = await httpClient.send(req).timeout(
      const Duration(seconds: 15),
    );
    return http.Response.fromStream(stream).timeout(
      const Duration(seconds: 15),
    );
  }

  bool isJson(http.Response response) =>
      (response.headers['content-type'] ?? '').toLowerCase().contains(
        'application/json',
      );

  int? before;
  int? logout;
  int? after;
  try {
    final initial = await request('GET', '/api/v1/logs');
    before = initial.statusCode;
    if (before != 200 || !isJson(initial)) {
      return W01RevocationProbeResult(
        beforeStatus: before,
        failureCode: 'active_bearer_not_verified',
      );
    }
    final signedOut = await request('POST', '/api/v1/auth/logout');
    logout = signedOut.statusCode;
    if (logout != 200 || !isJson(signedOut)) {
      return W01RevocationProbeResult(
        beforeStatus: before,
        logoutStatus: logout,
        failureCode: 'server_logout_not_confirmed',
      );
    }
    final replay = await request('GET', '/api/v1/logs');
    after = replay.statusCode;
    return W01RevocationProbeResult(
      beforeStatus: before,
      logoutStatus: logout,
      afterStatus: after,
      failureCode: (after == 401 && isJson(replay))
          ? null
          : 'old_bearer_not_rejected',
    );
  } catch (_) {
    // Avoid logging exception strings: network libraries may carry request
    // headers including the ephemeral bearer in their diagnostic objects.
    return W01RevocationProbeResult(
      beforeStatus: before,
      logoutStatus: logout,
      afterStatus: after,
      failureCode: 'transport_unavailable',
    );
  } finally {
    if (ownClient) httpClient.close();
  }
}
