import 'dart:typed_data';

import 'clinical_export_consent_contract.dart';

/// Disposable in-memory draft of FICTIONAL bytes only.
/// No disk, OS sharing, printing, network or genuine clinical authorization.
/// Zeroing Dart bytes is best effort, not secure OS/browser file deletion.
final class EphemeralClinicalExportDraft {
  EphemeralClinicalExportDraft._({
    required this.request,
    required this.consent,
    required Uint8List input,
  }) : _bytes = Uint8List.fromList(input);

  static const int maxSyntheticBytes = 262144; // 256 KiB fixtures only.

  final DoctorExportPreviewRequest request;
  final DoctorExportConsentDraft consent;
  Uint8List _bytes;
  bool _purged = false;
  bool _busy = false;

  static EphemeralClinicalExportDraft openFixture({
    required DoctorExportPreviewRequest request,
    required DoctorExportConsentDraft consent,
    required Uint8List syntheticBytes,
  }) {
    DoctorExportConsentPolicy.requireFixturePreview(
      request: request,
      consent: consent,
    );
    if (syntheticBytes.isEmpty || syntheticBytes.length > maxSyntheticBytes) {
      throw ArgumentError('CAL12: invalid fictional payload size');
    }
    return EphemeralClinicalExportDraft._(
      request: request,
      consent: consent,
      input: syntheticBytes,
    );
  }

  bool get isPurged => _purged;

  /// One invocation only. Validates consent against fresh UTC just before use.
  /// The borrowed bytes are overwritten even if inspection throws.
  Future<void> previewOnce({
    required DateTime nowUtc,
    required Future<void> Function(Uint8List borrowedBytes) inspect,
  }) async {
    if (_purged || _busy) {
      throw StateError('CAL12: draft already consumed, purged or busy');
    }
    _busy = true;
    try {
      final latest = DoctorExportPreviewRequest(
        currentOwnerScope: request.currentOwnerScope,
        reportOwnerScope: request.reportOwnerScope,
        recipientScope: request.recipientScope,
        notice: request.notice,
        purpose: request.purpose,
        channel: request.channel,
        category: request.category,
        periodStartUtc: request.periodStartUtc,
        periodEndUtc: request.periodEndUtc,
        nowUtc: nowUtc,
      );
      DoctorExportConsentPolicy.requireFixturePreview(
        request: latest,
        consent: consent,
      );
      await inspect(_bytes);
      if (_purged) {
        throw StateError('CAL12: draft revoked while preview was running');
      }
    } finally {
      purge();
      _busy = false;
    }
  }

  /// Safe if repeated or called while a preview is in progress.
  void revoke() => purge();
  void cancel() => purge();

  void purge() {
    if (_purged) return;
    _bytes.fillRange(0, _bytes.length, 0);
    _purged = true;
  }
}
