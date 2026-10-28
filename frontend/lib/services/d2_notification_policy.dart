/// D2 Web/PWA: deterministic *in-app preview* eligibility only.
///
/// This module cannot authorize delivery. No consumer is wired until patient-
/// scoped consent persistence, UI and external clinical/privacy gates pass.
/// A preview is neither a reminder nor an IAmina conversational message.
enum D2MessageChannel { reminder, inAppNotification, companionConversation }

enum D2NotificationSurface { inAppPreview, browserPush }

enum D2NotificationSource { governedProactiveObservation, unknown }

enum D2PreviewResult {
  eligibleForPreviewOnly,
  wrongChannel,
  deliveryUnavailable,
  patientScopeDenied,
  staleAuthSession,
  locked,
  consentDenied,
  unknownSource,
  clinicalAuthorityDenied,
  invalidEvidenceWindow,
  duplicate,
  cooldown,
}

/// Synthetic input contract. Never construct this from model-generated claims.
class D2NotificationCandidate {
  final D2MessageChannel channel;
  final D2NotificationSurface surface;
  final D2NotificationSource source;
  final int? authenticatedPatientId;
  final int? recordPatientId;
  final int capturedAuthEpoch;
  final int currentAuthEpoch;
  final bool isUnlocked;
  final bool explicitProactiveOptIn;
  final bool serverConsentConfirmed;
  final bool globalAiOptOut;
  final String evidenceId;
  final String sourceVersion;
  final String signature;
  final DateTime observedAt;
  final DateTime expiresAt;
  final DateTime now;
  final DateTime? lastPreviewAt;
  final Set<String> alreadyPreviewedSignatures;
  final bool hasEmergencyAuthority;
  final bool suggestsTreatmentChange;

  const D2NotificationCandidate({
    required this.channel,
    required this.surface,
    required this.source,
    required this.authenticatedPatientId,
    required this.recordPatientId,
    required this.capturedAuthEpoch,
    required this.currentAuthEpoch,
    required this.isUnlocked,
    required this.explicitProactiveOptIn,
    required this.serverConsentConfirmed,
    required this.globalAiOptOut,
    required this.evidenceId,
    required this.sourceVersion,
    required this.signature,
    required this.observedAt,
    required this.expiresAt,
    required this.now,
    required this.lastPreviewAt,
    required this.alreadyPreviewedSignatures,
    required this.hasEmergencyAuthority,
    required this.suggestsTreatmentChange,
  });
}

abstract final class D2NotificationPolicy {
  /// Only the deterministic backend's existing non-urgent rule is recognized.
  static const governedSourceVersion =
      'proactive.personal-response.lifecycle.v1';

  static const cooldown = Duration(hours: 24);

  /// Hard disabled regardless of OS permission, consent or caller input.
  /// No Service Worker, Push API, notification inbox or dispatch is wired.
  static bool get browserPushAvailable => false;

  /// This function is not an OS/in-app delivery authorization.
  /// Even [eligibleForPreviewOnly] cannot send, schedule or persist a message.
  static D2PreviewResult evaluateForInAppPreview(D2NotificationCandidate c) {
    if (c.channel != D2MessageChannel.inAppNotification) {
      return D2PreviewResult.wrongChannel;
    }
    if (c.surface != D2NotificationSurface.inAppPreview) {
      return D2PreviewResult.deliveryUnavailable;
    }
    if (c.authenticatedPatientId == null ||
        c.authenticatedPatientId! <= 0 ||
        c.recordPatientId != c.authenticatedPatientId) {
      return D2PreviewResult.patientScopeDenied;
    }
    if (c.capturedAuthEpoch != c.currentAuthEpoch) {
      return D2PreviewResult.staleAuthSession;
    }
    if (!c.isUnlocked) return D2PreviewResult.locked;
    if (!c.explicitProactiveOptIn ||
        !c.serverConsentConfirmed ||
        c.globalAiOptOut) {
      return D2PreviewResult.consentDenied;
    }
    if (c.source != D2NotificationSource.governedProactiveObservation ||
        c.sourceVersion != governedSourceVersion ||
        c.evidenceId.trim().isEmpty ||
        c.signature.trim().isEmpty) {
      return D2PreviewResult.unknownSource;
    }
    if (c.hasEmergencyAuthority || c.suggestsTreatmentChange) {
      return D2PreviewResult.clinicalAuthorityDenied;
    }
    if (c.observedAt.isAfter(c.now) ||
        !c.expiresAt.isAfter(c.now) ||
        !c.expiresAt.isAfter(c.observedAt)) {
      return D2PreviewResult.invalidEvidenceWindow;
    }
    if (c.alreadyPreviewedSignatures.contains(c.signature)) {
      return D2PreviewResult.duplicate;
    }
    final previous = c.lastPreviewAt;
    if (previous != null &&
        (previous.isAfter(c.now) || c.now.difference(previous) < cooldown)) {
      return D2PreviewResult.cooldown;
    }
    return D2PreviewResult.eligibleForPreviewOnly;
  }
}
