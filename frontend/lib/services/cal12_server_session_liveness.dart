import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;

import 'app_lock_service.dart';
import 'auth_epoch.dart';
import 'auth_service.dart';
import 'cal12_authenticated_vault_probe.dart';
import 'patient_vault_session_controller.dart';

/// CAL-12 liveness PRE-FLIGHT: live Django bearer check, no clinical export.
///
/// This is not a reusable capability and cannot authorize patient export.
/// The future real export endpoint must recheck bearer, consent and recipient
/// within its own transaction. There is no patient payload or upload here.
abstract final class Cal12ServerSessionLiveness {
  static const bool realPatientExportEnabled = false;
  static const _timeout = Duration(seconds: 8);

  static bool _safeOrigin(Uri origin) {
    final loopback = origin.host == 'localhost' ||
        origin.host == '127.0.0.1' ||
        origin.host == '::1';
    return origin.userInfo.isEmpty &&
        origin.host.isNotEmpty &&
        origin.query.isEmpty &&
        origin.fragment.isEmpty &&
        (origin.scheme == 'https' || (origin.scheme == 'http' && loopback));
  }

  static Future<bool> verifyOnce({
    required AuthService auth,
    required PatientVaultSessionController vault,
    required AppLockService appLock,
    http.Client? client,
  }) async {
    final snapshot = Cal12AuthenticatedVaultProbe.tryCapture(
      auth: auth,
      vault: vault,
      appLock: appLock,
    );
    if (snapshot == null) return false;

    final epoch = AuthService.authEpoch;
    final expectedAccountId = auth.boundNativeAccountId;
    final ownedClient = client == null;
    final transport = client ?? http.Client();

    try {
      // On Web use the current page's origin, not a configured remote backend.
      // For loopback FUE, the existing IAMINA local-backend exception applies.
      final origin = Uri.parse(resolveAuthApiOrigin(
        isWeb: kIsWeb,
        remoteAccountLogin: true,
        pageUri: Uri.base,
        configuredBaseUrl: kAuthBaseUrl,
        useConfiguredLoopbackBackend: true,
      ));
      if (!_safeOrigin(origin) || expectedAccountId == null) return false;

      final token = await auth.getIdToken();
      if (!snapshot.isCurrent ||
          epoch != AuthService.authEpoch ||
          token == null ||
          !token.startsWith('iamina.')) {
        return false;
      }

      final uri = origin.resolve('/api/v1/auth/session/verify');
      if (uri.origin != origin.origin) return false;
      final request = http.Request('GET', uri)
        ..followRedirects = false
        ..headers.addAll({
          'Authorization': 'Bearer $token',
          'Cache-Control': 'no-store',
          'Accept': 'application/json',
        });
      // Recheck immediately before dispatch, after token lookup and build.
      if (!snapshot.isCurrent) return false;
      final streamed = await transport.send(request).timeout(_timeout);
      final response =
          await http.Response.fromStream(streamed).timeout(_timeout);
      if (!snapshot.isCurrent ||
          epoch != AuthService.authEpoch ||
          response.statusCode != 200 ||
          !response.headers['cache-control'].toString().contains('no-store') ||
          !response.headers['content-type'].toString().contains('application/json')) {
        return false;
      }
      final result = jsonDecode(response.body);
      return snapshot.isCurrent &&
          result is Map<String, dynamic> &&
          result['active'] == true &&
          result['account_id'] == expectedAccountId;
    } catch (_) {
      // Network, malformed response, stale auth and revoked tokens fail closed.
      return false;
    } finally {
      snapshot.retire();
      if (ownedClient) transport.close();
    }
  }
}
