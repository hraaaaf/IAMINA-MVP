import 'synthetic_doctor_report.dart';

/// Fictional identities only: no actual account, patient or recipient IDs.
enum SyntheticVaultFixture { alpha, beta }
enum SyntheticRecipientFixture { doctorOne, doctorTwo }

/// A preview intention, not clinical export authorization.
enum SyntheticExportPurpose { doctorFollowUp }

final class SyntheticExportConsentFixture {
  const SyntheticExportConsentFixture({
    required this.owner,
    required this.recipient,
    required this.purpose,
    required this.grantedAtUtc,
    required this.expiresAtUtc,
    required this.explicitlyConfirmed,
    this.revokedAtUtc,
  });

  final SyntheticVaultFixture owner;
  final SyntheticRecipientFixture recipient;
  final SyntheticExportPurpose purpose;
  final DateTime grantedAtUtc;
  final DateTime expiresAtUtc;
  final DateTime? revokedAtUtc;
  final bool explicitlyConfirmed;
}

final class SyntheticDoctorPreviewIntent {
  const SyntheticDoctorPreviewIntent({
    required this.report,
    required this.reportOwner,
    required this.activeOwner,
    required this.recipient,
    required this.confirmedRecipient,
    required this.recipientConfirmedAtUtc,
    required this.requestedAtUtc,
    required this.consent,
  });

  final SyntheticDoctorReport report;
  final SyntheticVaultFixture reportOwner;
  final SyntheticVaultFixture activeOwner;
  final SyntheticRecipientFixture recipient;
  final SyntheticRecipientFixture confirmedRecipient;
  final DateTime recipientConfirmedAtUtc;
  final DateTime requestedAtUtc;
  final SyntheticExportConsentFixture consent;
}

/// Synthetic CAL-12 model exercise only. NEVER wire into ReportsScreen.
/// Does not perform download, print, email, OS Share or network requests.
/// It is not a medical/legal consent store or patient ownership verifier.
abstract final class SyntheticDoctorExportGate {
  static const bool patientExportEnabled = false;

  static String previewHtml({
    required SyntheticDoctorPreviewIntent intent,
    required String languageCode,
  }) {
    _requireAuthorizedFixture(intent);
    return SyntheticDoctorHtml.build(
      report: intent.report,
      languageCode: languageCode,
    );
  }

  static void _requireAuthorizedFixture(SyntheticDoctorPreviewIntent intent) {
    final consent = intent.consent;
    final now = intent.requestedAtUtc;
    if (!now.isUtc ||
        !intent.recipientConfirmedAtUtc.isUtc ||
        !consent.grantedAtUtc.isUtc ||
        !consent.expiresAtUtc.isUtc ||
        (consent.revokedAtUtc != null && !consent.revokedAtUtc!.isUtc)) {
      throw StateError('CAL12 synthetic: explicit UTC required');
    }
    if (intent.activeOwner != intent.reportOwner ||
        consent.owner != intent.activeOwner) {
      throw StateError('CAL12 synthetic: owner/session mismatch');
    }
    if (!consent.explicitlyConfirmed ||
        consent.purpose != SyntheticExportPurpose.doctorFollowUp) {
      throw StateError('CAL12 synthetic: explicit purpose consent missing');
    }
    if (intent.recipient != intent.confirmedRecipient ||
        intent.recipient != consent.recipient) {
      throw StateError('CAL12 synthetic: destination mismatch');
    }
    if (consent.expiresAtUtc.isBefore(consent.grantedAtUtc) ||
        consent.grantedAtUtc.isAfter(now) ||
        !now.isBefore(consent.expiresAtUtc)) {
      throw StateError('CAL12 synthetic: consent expired/not yet effective');
    }
    if (consent.revokedAtUtc != null &&
        !now.isBefore(consent.revokedAtUtc!)) {
      throw StateError('CAL12 synthetic: consent revoked');
    }
    if (intent.recipientConfirmedAtUtc.isBefore(consent.grantedAtUtc) ||
        intent.recipientConfirmedAtUtc.isAfter(now)) {
      throw StateError('CAL12 synthetic: recipient confirmation invalid');
    }
    if (intent.report.generatedAtUtc.isAfter(now)) {
      throw StateError('CAL12 synthetic: report is from the future');
    }
  }
}
