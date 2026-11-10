import 'dart:convert';

import 'package:crypto/crypto.dart';

/// CAL-12 technical consent contract for a future clinical export.
/// Never connected to patient UI, storage, email, OS share or network.
enum DoctorExportPurpose { followUpWithClinician }
enum DoctorExportChannel { localPreview, secureRecipientDelivery }
enum DoctorExportDataCategory { syntheticManualReadings, clinicalMeasurements }

/// The only notices currently defined are NOT approved for real patients.
final class DoctorExportNoticeDraft {
  const DoctorExportNoticeDraft({
    required this.version,
    required this.locale,
    required this.sha256Hex,
  });

  final String version;
  final String locale;
  final String sha256Hex;
}

/// Sample text to exercise versioned digest binding; NOT legal or clinical copy.
abstract final class DoctorExportDraftNoticeCatalog {
  static const version = 'CAL12-DRAFT-2026-11-10.1';
  static const _copy = <String, String>{
    'fr': 'DÉMONSTRATION UNIQUEMENT. Prévisualiser des mesures '
        'fictives pour un médecin fictif. Aucun document envoyé.',
    'en': 'DEMONSTRATION ONLY. Preview fictional readings '
        'for a fictional doctor. No document is sent.',
    'ar': 'للتجربة فقط. معاينة قياسات افتراضية لطبيب افتراضي. '
        'لا يتم إرسال أي مستند.',
  };

  static DoctorExportNoticeDraft forLocale(String locale) {
    final copy = _copy[locale];
    if (copy == null) {
      throw ArgumentError.value(locale, 'locale', 'Unsupported draft notice');
    }
    return DoctorExportNoticeDraft(
      version: version,
      locale: locale,
      sha256Hex: sha256.convert(utf8.encode(copy)).toString(),
    );
  }

  static bool isCurrent(DoctorExportNoticeDraft candidate) {
    try {
      final current = forLocale(candidate.locale);
      return candidate.version == current.version &&
          candidate.sha256Hex == current.sha256Hex;
    } on ArgumentError {
      return false;
    }
  }
}

/// Scope and recipient IDs below are fictional, never a real patient/doctor.
final class DoctorExportConsentDraft {
  const DoctorExportConsentDraft({
    required this.ownerScope,
    required this.recipientScope,
    required this.notice,
    required this.purpose,
    required this.channel,
    required this.category,
    required this.periodStartUtc,
    required this.periodEndUtc,
    required this.grantedAtUtc,
    required this.expiresAtUtc,
    required this.recipientConfirmedAtUtc,
    required this.explicitlyAgreed,
    this.revokedAtUtc,
  });

  final String ownerScope;
  final String recipientScope;
  final DoctorExportNoticeDraft notice;
  final DoctorExportPurpose purpose;
  final DoctorExportChannel channel;
  final DoctorExportDataCategory category;
  final DateTime periodStartUtc;
  final DateTime periodEndUtc;
  final DateTime grantedAtUtc;
  final DateTime expiresAtUtc;
  final DateTime recipientConfirmedAtUtc;
  final bool explicitlyAgreed;
  final DateTime? revokedAtUtc;
}

final class DoctorExportPreviewRequest {
  const DoctorExportPreviewRequest({
    required this.currentOwnerScope,
    required this.reportOwnerScope,
    required this.recipientScope,
    required this.notice,
    required this.purpose,
    required this.channel,
    required this.category,
    required this.periodStartUtc,
    required this.periodEndUtc,
    required this.nowUtc,
  });

  final String currentOwnerScope;
  final String reportOwnerScope;
  final String recipientScope;
  final DoctorExportNoticeDraft notice;
  final DoctorExportPurpose purpose;
  final DoctorExportChannel channel;
  final DoctorExportDataCategory category;
  final DateTime periodStartUtc;
  final DateTime periodEndUtc;
  final DateTime nowUtc;
}

enum DoctorExportDenyReason {
  nonFixtureIdentity,
  patientExportDisabled,
  ownerMismatch,
  recipientMismatch,
  noticeChanged,
  unsupportedPurposeOrCategory,
  incorrectDataWindow,
  utcMissing,
  consentNotConfirmed,
  consentExpiredOrFuture,
  consentRevoked,
  destinationConfirmationInvalid,
}

/// Draft, fail-closed policy: never authorizes a patient or real delivery.
abstract final class DoctorExportConsentPolicy {
  static const bool realPatientExportEnabled = false;
  static const maxDraftConsentDuration = Duration(minutes: 15);
  static final _owner = RegExp(r'^fixture:vault:[a-z0-9_-]{1,32}$');
  static final _recipient = RegExp(r'^fixture:doctor:[a-z0-9_-]{1,32}$');

  static DoctorExportDenyReason? evaluateFixturePreview({
    required DoctorExportPreviewRequest request,
    required DoctorExportConsentDraft consent,
  }) {
    if (!_owner.hasMatch(request.currentOwnerScope) ||
        !_owner.hasMatch(request.reportOwnerScope) ||
        !_owner.hasMatch(consent.ownerScope) ||
        !_recipient.hasMatch(request.recipientScope) ||
        !_recipient.hasMatch(consent.recipientScope)) {
      return DoctorExportDenyReason.nonFixtureIdentity;
    }
    if (request.channel != DoctorExportChannel.localPreview ||
        consent.channel != DoctorExportChannel.localPreview) {
      return DoctorExportDenyReason.patientExportDisabled;
    }
    if (request.currentOwnerScope != request.reportOwnerScope ||
        request.currentOwnerScope != consent.ownerScope) {
      return DoctorExportDenyReason.ownerMismatch;
    }
    if (request.recipientScope != consent.recipientScope) {
      return DoctorExportDenyReason.recipientMismatch;
    }
    if (!DoctorExportDraftNoticeCatalog.isCurrent(request.notice) ||
        !DoctorExportDraftNoticeCatalog.isCurrent(consent.notice) ||
        request.notice.locale != consent.notice.locale) {
      return DoctorExportDenyReason.noticeChanged;
    }
    if (request.purpose != DoctorExportPurpose.followUpWithClinician ||
        consent.purpose != request.purpose ||
        request.category != DoctorExportDataCategory.syntheticManualReadings ||
        consent.category != request.category) {
      return DoctorExportDenyReason.unsupportedPurposeOrCategory;
    }
    if (!request.periodStartUtc.isUtc ||
        !request.periodEndUtc.isUtc ||
        request.periodStartUtc.isAfter(request.periodEndUtc) ||
        request.periodStartUtc != consent.periodStartUtc ||
        request.periodEndUtc != consent.periodEndUtc) {
      return DoctorExportDenyReason.incorrectDataWindow;
    }
    if (!request.nowUtc.isUtc ||
        !consent.periodStartUtc.isUtc ||
        !consent.periodEndUtc.isUtc ||
        !consent.grantedAtUtc.isUtc ||
        !consent.expiresAtUtc.isUtc ||
        !consent.recipientConfirmedAtUtc.isUtc ||
        (consent.revokedAtUtc != null && !consent.revokedAtUtc!.isUtc)) {
      return DoctorExportDenyReason.utcMissing;
    }
    if (!consent.explicitlyAgreed) {
      return DoctorExportDenyReason.consentNotConfirmed;
    }
    if (consent.expiresAtUtc.isBefore(consent.grantedAtUtc) ||
        consent.expiresAtUtc.difference(consent.grantedAtUtc) >
            maxDraftConsentDuration ||
        consent.grantedAtUtc.isAfter(request.nowUtc) ||
        !request.nowUtc.isBefore(consent.expiresAtUtc)) {
      return DoctorExportDenyReason.consentExpiredOrFuture;
    }
    // Even a future-dated withdrawal invalidates consent: fail closed.
    if (consent.revokedAtUtc != null) {
      return DoctorExportDenyReason.consentRevoked;
    }
    if (consent.recipientConfirmedAtUtc.isBefore(consent.grantedAtUtc) ||
        consent.recipientConfirmedAtUtc.isAfter(request.nowUtc)) {
      return DoctorExportDenyReason.destinationConfirmationInvalid;
    }
    return null;
  }

  static void requireFixturePreview({
    required DoctorExportPreviewRequest request,
    required DoctorExportConsentDraft consent,
  }) {
    final failure = evaluateFixturePreview(request: request, consent: consent);
    if (failure != null) {
      throw StateError('CAL12_DRAFT_DENIED:' + failure.name);
    }
  }
}
