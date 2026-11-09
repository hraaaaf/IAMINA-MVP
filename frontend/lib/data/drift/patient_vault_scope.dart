/// D7 — namespace for entire local clinical vault, not only PatientProfiles.
///
/// Names separate remote Django patients, device-only enrollment and audit.
/// This is an isolated namespace constructor; it does not grant authorization
/// and does not assign legacy "amina" data to any person.
///
/// Never derive account scope from a bearer token, Firebase hashCode, email,
/// diagnosis, IP, or the old local fallback userId=1.
final class PatientVaultScope {
  final String databaseName;
  final int? nativeDjangoUserId;

  const PatientVaultScope._(this.databaseName, {this.nativeDjangoUserId});

  factory PatientVaultScope.nativeDjango(int userId) {
    if (userId <= 0) {
      throw ArgumentError.value(userId, 'userId', 'Invalid Django patient ID');
    }
    return PatientVaultScope._(
      'amina_vault_v1_native_$userId',
      nativeDjangoUserId: userId,
    );
  }

  factory PatientVaultScope.deviceLocal(String deviceId) {
    final normalized = deviceId.toLowerCase();
    final uuidV4 = RegExp(
      r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    );
    if (!uuidV4.hasMatch(normalized)) {
      throw ArgumentError.value(
        deviceId, 'deviceId', 'Stable enrolled device UUIDv4 required',
      );
    }
    return PatientVaultScope._(
      'amina_vault_v1_device_${normalized.replaceAll('-', '')}',
    );
  }

  factory PatientVaultScope.auditOnly() =>
      const PatientVaultScope._('amina_vault_v1_audit');

  @override
  String toString() => 'PatientVaultScope(databaseName: $databaseName)';
}
