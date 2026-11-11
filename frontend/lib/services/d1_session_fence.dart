import '../data/drift/patient_vault_scope.dart';

/// D1-C experimental operation fence; NOT an authentication or encryption
/// primitive by itself. It cannot be used as proof that a vault is protected.
/// Never publish an async result unless the SAME current epoch and owner
/// still match the original ticket.
final class D1SessionFence {
  final String _owner;
  final int _issuedEpoch;
  int _generation = 0;
  bool _retired = false;

  D1SessionFence(PatientVaultScope scope, int authEpoch)
    : _owner = scope.databaseName,
      _issuedEpoch = authEpoch {
    if (authEpoch < 0 ||
        !(scope.nativeDjangoUserId != null ||
          scope.databaseName.startsWith('amina_vault_v1_device_'))) {
      throw StateError('D1_CLINICAL_SESSION_AUTH_REQUIRED');
    }
  }

  bool get isRetired => _retired;

  D1SessionTicket beginOperation({
    required PatientVaultScope currentScope,
    required int currentAuthEpoch,
  }) {
    _assertCurrent(currentScope, currentAuthEpoch);
    return D1SessionTicket._(_owner, _issuedEpoch, _generation);
  }

  bool canPublish(
    D1SessionTicket ticket, {
    required PatientVaultScope currentScope,
    required int currentAuthEpoch,
  }) =>
      !_retired &&
      _owner == currentScope.databaseName &&
      currentAuthEpoch == _issuedEpoch &&
      ticket._owner == _owner &&
      ticket._epoch == _issuedEpoch &&
      ticket._generation == _generation;

  void assertCanPublish(
    D1SessionTicket ticket, {
    required PatientVaultScope currentScope,
    required int currentAuthEpoch,
  }) {
    if (!canPublish(
      ticket, currentScope: currentScope, currentAuthEpoch: currentAuthEpoch,
    )) {
      throw StateError('D1_RETIRED_OR_FOREIGN_OPERATION');
    }
  }

  void _assertCurrent(PatientVaultScope scope, int epoch) {
    if (_retired || scope.databaseName != _owner || epoch != _issuedEpoch) {
      throw StateError('D1_SESSION_NOT_CURRENT');
    }
  }

  /// Must be called synchronously at logout/switch/lock revocation, before
  /// any await or provider publication. A retired fence cannot be revived.
  void retire() {
    _retired = true;
    _generation++;
  }
}

final class D1SessionTicket {
  final String _owner;
  final int _epoch;
  final int _generation;
  const D1SessionTicket._(this._owner, this._epoch, this._generation);

  @override
  String toString() => 'D1SessionTicket(redacted)';
}
