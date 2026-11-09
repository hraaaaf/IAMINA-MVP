import 'consent_service.dart';

/// Fail-closed consent withdrawal. An exact owner-scoped local marker must be
/// persisted before attempting the remote DELETE. Missing server confirmation
/// NEVER results in a "withdrawn" success message. Pending state survives a
/// reload and exposes the retry action for the same patient vault.
enum D7WithdrawalResult { confirmed, awaitingServer, localSafetyFailed }

Future<D7WithdrawalResult> withdrawD7AiConsent({
  required ConsentService consent,
  required Future<void> Function() markPending,
  required Future<bool> Function() revokeServer,
  required Future<void> Function() clearEvidence,
  required Future<void> Function() clearLocalRecord,
  required Future<void> Function() clearPending,
}) async {
  consent.markWithdrawalPending(); // prevent further local AI immediately
  try {
    await markPending(); // durable same-vault privacy stop before network
  } catch (_) {
    return D7WithdrawalResult.localSafetyFailed;
  }

  bool serverRevoked = false;
  try {
    serverRevoked = await revokeServer();
  } catch (_) {
    // Keep owner-scoped pending marker: never invent a remote acknowledgement.
  }
  if (!serverRevoked) return D7WithdrawalResult.awaitingServer;

  try {
    await clearEvidence();
    await clearLocalRecord();
    await clearPending(); // only after all three preceding gates are confirmed
    consent.markWithdrawalConfirmed();
    return D7WithdrawalResult.confirmed;
  } catch (_) {
    // The persisted pending marker survives process restart. Retry is possible.
    return D7WithdrawalResult.localSafetyFailed;
  }
}
