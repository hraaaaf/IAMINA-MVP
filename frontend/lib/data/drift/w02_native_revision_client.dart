import 'dart:convert';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;

import '../../services/auth_service.dart';
import '../../services/preview_api_origin.dart';

/// W02/D10 isolated Preview integration seam. Neither AppDatabase nor any
/// patient route imports this file. No clinical write access is granted.
///
/// The interface is intentionally narrow so synthetic tests can simulate
/// A -> logout -> B while the real adapter uses AuthService's cross-tab
/// credential storage checks and auth epoch.
abstract interface class W02NativePrincipalSource {
  int get epoch;
  int? get nativeAccountId;
  bool get remoteCredentialVerified;
  bool get isAudit;
  Future<String?> readBearer();
  Future<String?> readVaultNamespace();
}

final class W02AuthServicePrincipalSource implements W02NativePrincipalSource {
  final AuthService _auth;
  W02AuthServicePrincipalSource(this._auth);

  @override
  int get epoch => AuthService.authEpoch;

  @override
  int? get nativeAccountId => _auth.boundNativeAccountId;

  @override
  bool get remoteCredentialVerified => _auth.isRemoteCredentialVerified;

  @override
  bool get isAudit => _auth.isAuditSession;

  @override
  Future<String?> readBearer() => _auth.getIdToken();

  @override
  Future<String?> readVaultNamespace() async =>
      (await _auth.resolvePatientVaultScope())?.databaseName;
}

final class W02RevisionClientException implements Exception {
  final String code;
  const W02RevisionClientException(this.code);
  @override
  String toString() => 'W02RevisionClientException($code)';
}

/// Pinned to Web Preview, not a general-purpose arbitrary URL fetcher.
/// In production no route imports or instantiates this class.
final class W02NativeRevisionClient {
  static final _host = RegExp(
    r'^iamina-review-[a-z0-9-]+-achraf-benmoussa-s-projects\.vercel\.app$',
  );
  static final _nativeBearer = RegExp(
    r'^iamina\.[A-Za-z0-9_.-]+:[A-Za-z0-9]+:[A-Za-z0-9_-]+$',
  );
  static final _slot = RegExp(r'^[A-Za-z0-9_-]{43}$');
  static final _sha256 = RegExp(r'^[0-9a-f]{64}$');
  static const _endpoint = '/api/v1/w02/vault-revision/';

  final W02NativePrincipalSource _identity;
  final http.Client _http;
  final Uri _origin;
  final int _capturedEpoch;
  final int _userId;
  final String vaultId;
  final String _capturedBearer;

  W02NativeRevisionClient._(
    this._identity,
    this._http,
    this._origin,
    this._capturedEpoch,
    this._userId,
    this.vaultId,
    this._capturedBearer,
  );

  /// Production construction requires the existing explicit Preview transport
  /// compile-time gate, HTTPS and the exact IAMINA Web Preview hostname family.
  /// Test-only construction can inject a fake principal + HTTPS mock client.
  static Future<W02NativeRevisionClient> capture({
    required W02NativePrincipalSource identity,
    required http.Client client,
    required Uri origin,
    bool syntheticTestOnly = false,
  }) async {
    if (!syntheticTestOnly && (!kIsWeb || !kIaminaPreviewSameOriginApi)) {
      throw const W02RevisionClientException('preview_gate_closed');
    }
    if (origin.scheme != 'https' || origin.hasPort ||
        origin.userInfo.isNotEmpty || origin.path != '' ||
        origin.hasQuery || origin.hasFragment ||
        (!syntheticTestOnly && !_host.hasMatch(origin.host)) ||
        (syntheticTestOnly && origin.host != 'test-only.invalid')) {
      throw const W02RevisionClientException('preview_origin_rejected');
    }
    final epoch = identity.epoch;
    final account = identity.nativeAccountId;
    if (identity.isAudit || !identity.remoteCredentialVerified ||
        account == null || account < 1) {
      throw const W02RevisionClientException('native_identity_not_verified');
    }
    final name = 'amina_vault_v1_native_$account';
    final token = await identity.readBearer();
    if (identity.epoch != epoch ||
        identity.nativeAccountId != account ||
        !identity.remoteCredentialVerified ||
        identity.isAudit ||
        token == null || !_nativeBearer.hasMatch(token)) {
      throw const W02RevisionClientException('owner_changed_during_capture');
    }
    final scope = await identity.readVaultNamespace();
    if (identity.epoch != epoch ||
        identity.nativeAccountId != account ||
        !identity.remoteCredentialVerified ||
        identity.isAudit ||
        scope != name) {
      throw const W02RevisionClientException('vault_scope_not_verified');
    }
    return W02NativeRevisionClient._(
      identity, client, origin, epoch, account, name, token,
    );
  }

  Future<String> _currentBearer() async {
    if (_identity.epoch != _capturedEpoch ||
        _identity.nativeAccountId != _userId ||
        !_identity.remoteCredentialVerified || _identity.isAudit) {
      throw const W02RevisionClientException('owner_session_changed');
    }
    final bearer = await _identity.readBearer();
    if (_identity.epoch != _capturedEpoch ||
        _identity.nativeAccountId != _userId ||
        !_identity.remoteCredentialVerified || _identity.isAudit ||
        bearer != _capturedBearer || !_nativeBearer.hasMatch(bearer ?? '')) {
      throw const W02RevisionClientException('owner_session_changed');
    }
    final scope = await _identity.readVaultNamespace();
    if (_identity.epoch != _capturedEpoch ||
        _identity.nativeAccountId != _userId ||
        !_identity.remoteCredentialVerified || _identity.isAudit ||
        scope != vaultId) {
      throw const W02RevisionClientException('owner_session_changed');
    }
    return bearer!;
  }

  Future<Map<String, dynamic>> _request(
    String endpoint, {
    Map<String, Object>? body,
  }) async {
    final bearer = await _currentBearer();
    final uri = _origin.resolve('$_endpoint$endpoint');
    http.Response response;
    try {
      if (body == null) {
        response = await _http.get(
          uri, headers: {'Authorization': 'Bearer $bearer',
                         'Accept': 'application/json'},
        ).timeout(const Duration(seconds: 12));
      } else {
        response = await _http.post(
          uri,
          headers: {'Authorization': 'Bearer $bearer',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'},
          body: jsonEncode(body),
        ).timeout(const Duration(seconds: 12));
      }
    } catch (_) {
      // Never disclose HTTP exception fields, raw payload, tokens or origin.
      throw const W02RevisionClientException('authority_unavailable');
    }
    // Recheck owner through cross-tab secure storage after the response:
    // an old response must never become the current account's metadata.
    await _currentBearer();
    if (response.statusCode != 200 ||
        response.bodyBytes.length > 8192 ||
        !(response.headers['content-type'] ?? '').toLowerCase()
            .contains('application/json')) {
      throw const W02RevisionClientException('authority_rejected');
    }
    Object? payload;
    try {
      payload = jsonDecode(response.body);
    } catch (_) {
      throw const W02RevisionClientException('invalid_anchor_response');
    }
    if (payload is! Map<String, dynamic> || payload['vault_id'] != vaultId) {
      throw const W02RevisionClientException('verified_scope_mismatch');
    }
    return payload;
  }

  Future<Map<String, dynamic>> state() async {
    final value = await _request('state');
    final status = value['status'];
    final rev = value['committed_revision'];
    final floorHash = value['committed_envelope_sha256'];
    final pendingRev = value['pending_revision'];
    final pendingTicket = value['pending_ticket'];
    final slot = value['slot'];
    if (!['uninitialized', 'ready', 'pending'].contains(status) ||
        rev is! int || rev < 0 ||
        (status == 'uninitialized' &&
            (slot != null || rev != 0 ||
             pendingRev != null || pendingTicket != null)) ||
        (status != 'uninitialized' &&
            (slot is! String || !_slot.hasMatch(slot))) ||
        floorHash is! String ||
        (rev == 0 ? floorHash.isNotEmpty : !_sha256.hasMatch(floorHash)) ||
        (status == 'pending' &&
            (pendingRev is! int || pendingRev != rev + 1 ||
             pendingTicket is! String || !_slot.hasMatch(pendingTicket))) ||
        (status == 'ready' &&
            (pendingRev != null || pendingTicket != null))) {
      throw const W02RevisionClientException('invalid_anchor_state');
    }
    // Exposing a pending state is not permission to load any local snapshot.
    return value;
  }

  Future<Map<String, dynamic>> reserve({
    required String slot,
    required int expectedRevision,
  }) async {
    if (!_slot.hasMatch(slot) || expectedRevision < 0) {
      throw const W02RevisionClientException('invalid_reservation');
    }
    final value = await _request('reserve', body: {
      'slot': slot, 'expected_revision': expectedRevision,
    });
    if (value['revision'] != expectedRevision + 1 ||
        value['ticket'] is! String || !_slot.hasMatch(value['ticket'])) {
      throw const W02RevisionClientException('invalid_reservation_receipt');
    }
    return value;
  }

  Future<Map<String, dynamic>> finalize({
    required String slot,
    required int revision,
    required String ticket,
    required String envelopeSha256,
  }) async {
    if (!_slot.hasMatch(slot) || revision < 1 ||
        !_slot.hasMatch(ticket) || !_sha256.hasMatch(envelopeSha256)) {
      throw const W02RevisionClientException('invalid_finalization');
    }
    final value = await _request('finalize', body: {
      'slot': slot, 'revision': revision, 'ticket': ticket,
      'envelope_sha256': envelopeSha256,
    });
    if (value['status'] != 'ready' ||
        value['committed_revision'] != revision ||
        value['committed_envelope_sha256'] != envelopeSha256) {
      throw const W02RevisionClientException('invalid_finalization_receipt');
    }
    return value;
  }
}
