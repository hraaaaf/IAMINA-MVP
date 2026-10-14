import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

/// D9 server assertion only. It never authorizes AI, clinical uploads or
/// adoption of an unrelated patient's Drift profile.
final class D9FirstUseProof {
  final int ownerUserId;
  final bool completed;
  final DateTime? completedAt;

  const D9FirstUseProof({
    required this.ownerUserId,
    required this.completed,
    required this.completedAt,
  });

  static D9FirstUseProof? parse(Object? body, {required int expectedOwner}) {
    if (expectedOwner <= 0 || body is! Map || body['version'] != 1 ||
        body['owner_user_id'] != expectedOwner ||
        body['completed'] is! bool) {
      return null;
    }
    final completed = body['completed'] as bool;
    final stamp = body['completed_at'];
    if (!completed && stamp == null) {
      return D9FirstUseProof(
        ownerUserId: expectedOwner, completed: false, completedAt: null,
      );
    }
    if (!completed || stamp is! String ||
        !RegExp(r'(Z|[+-][0-9]{2}:[0-9]{2})$').hasMatch(stamp)) {
      return null;
    }
    final parsed = DateTime.tryParse(stamp)?.toUtc();
    return parsed == null
        ? null
        : D9FirstUseProof(
            ownerUserId: expectedOwner, completed: true, completedAt: parsed,
          );
  }
}

/// A safe, independent D9 transport to be wired at the patient-vault host.
///
/// An unknown proof (null) must NOT be interpreted as first-use completion
/// or as a first-use denial. It means that the authenticated server result
/// has not been verified for this exact patient/session yet.
final class D9FirstUseTransport {
  final Uri baseUri;
  final http.Client client;
  final Future<String?> Function() readBearer;
  final bool Function() hasNativeCredential;
  final bool Function() appLockUnlocked;
  final int? Function() activePatientOwner;
  final int Function() authEpoch;
  final int Function() vaultGeneration;
  final Duration timeout;

  const D9FirstUseTransport({
    required this.baseUri,
    required this.client,
    required this.readBearer,
    required this.hasNativeCredential,
    required this.appLockUnlocked,
    required this.activePatientOwner,
    required this.authEpoch,
    required this.vaultGeneration,
    this.timeout = const Duration(seconds: 8),
  });

  bool _hasSafeOrigin() {
    if (baseUri.host.isEmpty || baseUri.userInfo.isNotEmpty) return false;
    if (baseUri.scheme == 'https') return true;
    return baseUri.scheme == 'http' &&
        const <String>['localhost', '127.0.0.1', '::1']
            .contains(baseUri.host);
  }

  bool _authorized(int owner, int epoch, int generation) =>
      _hasSafeOrigin() &&
      owner > 0 &&
      hasNativeCredential() &&
      appLockUnlocked() &&
      activePatientOwner() == owner &&
      authEpoch() == epoch &&
      vaultGeneration() == generation;

  Future<D9FirstUseProof?> fetch() => _send(confirm: false);

  /// Invoke ONLY after a successful explicit local first-use save. The server
  /// verifies owner identity. Confirmation is NEVER inferred from GET /profile.
  Future<D9FirstUseProof?> confirmSavedFirstUse() => _send(confirm: true);

  Future<D9FirstUseProof?> _send({required bool confirm}) async {
    final owner = activePatientOwner();
    final epoch = authEpoch();
    final generation = vaultGeneration();
    if (owner == null || !_authorized(owner, epoch, generation)) return null;

    try {
      final bearer = await readBearer();
      if (bearer == null || !bearer.startsWith('iamina.') ||
          !_authorized(owner, epoch, generation)) {
        return null;
      }

      final uri = baseUri.resolve('/api/v1/profile/first-use');
      // Do not automatically follow redirects carrying the bearer. Use a
      // per-request redirect policy, rather than Client.get/post defaults.
      final request = http.Request(confirm ? 'POST' : 'GET', uri)
        ..followRedirects = false
        ..headers['Authorization'] = 'Bearer $bearer';
      if (confirm) {
        request.headers['Content-Type'] = 'application/json';
        request.body = jsonEncode(<String, Object>{
          'version': 1,
          'confirmed': true,
        });
      }
      final response = await (() async {
        final stream = await client.send(request);
        return http.Response.fromStream(stream);
      })().timeout(timeout);

      if (!_authorized(owner, epoch, generation) ||
          response.statusCode != 200) {
        return null;
      }
      final proof = D9FirstUseProof.parse(
        jsonDecode(response.body), expectedOwner: owner,
      );
      return confirm && proof?.completed != true ? null : proof;
    } catch (_) {
      // Offline, revoked bearer, malformed JSON, timeout, disposed client:
      // no speculative first-use completion and never a stale patient result.
      return null;
    }
  }
}
