/// W02-F09-C8: UNMOUNTED Web-only session coordinator candidate.
///
/// Never imported by the active AuthService/router. This contains only a
/// short-lived bearer in RAM: no secure-storage, IndexedDB, localStorage,
/// native bearer, Firebase or patient-vault owner binding. Closing/reloading
/// a tab always starts LOCKED. The caller must independently prove a C7
/// backend response before supplying a CandidateWebRefreshReply.
/// The verifiedByBackend flag below is TEST scaffolding, NOT cryptography.
import 'dart:async';

import 'package:flutter/foundation.dart';

import 'web_refresh_c8_signal_contract.dart';
import 'web_refresh_c8_signal_stub.dart'
    if (dart.library.html) 'web_refresh_c8_signal_web.dart' as platform;

class CandidateWebRefreshReply {
  const CandidateWebRefreshReply({
    required this.accessBearer,
    required this.expiresInSeconds,
  });

  final String accessBearer;
  final int expiresInSeconds;
}

class WebRefreshC8Coordinator extends ChangeNotifier {
  WebRefreshC8Coordinator({
    required this.enabled,
    required this.refreshTransport,
    required this.logoutTransport,
    WebRefreshC8SignalBus? signalBus,
    DateTime Function()? clock,
  })  : _signalBus = signalBus ?? platform.createC8SignalBus(),
        _clock = clock ?? DateTime.now {
    if (enabled) {
      _signalBus.listen(() => _clearMemory());
    }
  }

  final bool enabled;
  final Future<CandidateWebRefreshReply> Function() refreshTransport;
  final Future<bool> Function() logoutTransport;
  final WebRefreshC8SignalBus _signalBus;
  final DateTime Function() _clock;

  String? _bearer;
  DateTime? _expiry;
  Future<String?>? _pending;
  int _epoch = 0;
  bool _revoked = true;
  bool _disposed = false;

  static final _tokenPattern =
      RegExp(r'^iamina-web\.[A-Za-z0-9_.:-]{24,2040}$');

  bool _valid(CandidateWebRefreshReply data) {
    return _tokenPattern.hasMatch(data.accessBearer) &&
        data.expiresInSeconds > 0 &&
        data.expiresInSeconds <= 900;
  }

  void _clearMemory() {
    _epoch += 1;
    _revoked = true;
    _bearer = null;
    _expiry = null;
    if (!_disposed) notifyListeners();
  }

  bool get hasMemoryAccess => getMemoryBearer() != null;

  String? getMemoryBearer() {
    if (!enabled || _revoked || _disposed || _bearer == null) return null;
    if (_expiry == null || !_clock().isBefore(_expiry!)) {
      _clearMemory();
      return null;
    }
    return _bearer;
  }

  /// A verified upstream response is a PRECONDITION, not established here.
  bool bootstrapVerifiedCandidate(
    CandidateWebRefreshReply reply, {
    required bool verifiedByBackend,
  }) {
    if (!enabled || _disposed || !verifiedByBackend || !_valid(reply)) {
      return false;
    }
    _epoch += 1;
    _revoked = false;
    _bearer = reply.accessBearer;
    _expiry = _clock().add(Duration(seconds: reply.expiresInSeconds));
    notifyListeners();
    return true;
  }

  Future<String?> refresh() {
    if (!enabled || _disposed || _revoked || getMemoryBearer() == null) {
      return Future<String?>.value(null);
    }
    final existing = _pending;
    if (existing != null) return existing;
    final epoch = _epoch;

    Future<String?> perform() async {
      try {
        final reply = await refreshTransport();
        // A logout or a cross-tab event wins against any late network reply.
        if (_disposed || _revoked || epoch != _epoch) return null;
        if (!_valid(reply)) {
          _clearMemory();
          _signalBus.broadcastRevocation();
          return null;
        }
        _bearer = reply.accessBearer;
        _expiry = _clock().add(Duration(seconds: reply.expiresInSeconds));
        notifyListeners();
        return _bearer;
      } catch (_) {
        if (!_disposed && epoch == _epoch) {
          _clearMemory();
          _signalBus.broadcastRevocation();
        }
        return null;
      }
    }

    final future = perform();
    _pending = future;
    unawaited(future.whenComplete(() {
      if (identical(_pending, future)) _pending = null;
    }));
    return future;
  }

  /// Local revocation is synchronous; network failures can NEVER restore it.
  Future<bool> signOut() async {
    if (_disposed) return false;
    _clearMemory();
    _signalBus.broadcastRevocation();
    try {
      return await logoutTransport();
    } catch (_) {
      // The server may still honor an old access token until it expires.
      // Never report remote revocation as confirmed after a network failure.
      return false;
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _clearMemory();
    _signalBus.dispose();
    super.dispose();
  }
}
