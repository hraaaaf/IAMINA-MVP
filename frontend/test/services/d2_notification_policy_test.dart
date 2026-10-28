import 'package:amina/services/d2_notification_policy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final now = DateTime.utc(2026, 10, 20, 12);

  D2NotificationCandidate sample({
    D2MessageChannel channel = D2MessageChannel.inAppNotification,
    D2NotificationSurface surface = D2NotificationSurface.inAppPreview,
    D2NotificationSource source =
        D2NotificationSource.governedProactiveObservation,
    int? authenticatedPatientId = 17,
    int? recordPatientId = 17,
    int capturedAuthEpoch = 9,
    int currentAuthEpoch = 9,
    bool isUnlocked = true,
    bool explicitProactiveOptIn = true,
    bool serverConsentConfirmed = true,
    bool globalAiOptOut = false,
    String evidenceId = 'deterministic-evidence',
    String sourceVersion = D2NotificationPolicy.governedSourceVersion,
    String signature = 'approved-source-signature',
    DateTime? observedAt,
    DateTime? expiresAt,
    DateTime? lastPreviewAt,
    Set<String> alreadyPreviewedSignatures = const <String>{},
    bool hasEmergencyAuthority = false,
    bool suggestsTreatmentChange = false,
  }) =>
      D2NotificationCandidate(
        channel: channel,
        surface: surface,
        source: source,
        authenticatedPatientId: authenticatedPatientId,
        recordPatientId: recordPatientId,
        capturedAuthEpoch: capturedAuthEpoch,
        currentAuthEpoch: currentAuthEpoch,
        isUnlocked: isUnlocked,
        explicitProactiveOptIn: explicitProactiveOptIn,
        serverConsentConfirmed: serverConsentConfirmed,
        globalAiOptOut: globalAiOptOut,
        evidenceId: evidenceId,
        sourceVersion: sourceVersion,
        signature: signature,
        observedAt: observedAt ?? now.subtract(const Duration(hours: 1)),
        expiresAt: expiresAt ?? now.add(const Duration(hours: 1)),
        now: now,
        lastPreviewAt: lastPreviewAt,
        alreadyPreviewedSignatures: alreadyPreviewedSignatures,
        hasEmergencyAuthority: hasEmergencyAuthority,
        suggestsTreatmentChange: suggestsTreatmentChange,
      );

  D2PreviewResult decision(D2NotificationCandidate candidate) =>
      D2NotificationPolicy.evaluateForInAppPreview(candidate);

  test('a governed observation qualifies for preview only, never dispatch', () {
    expect(decision(sample()), D2PreviewResult.eligibleForPreviewOnly);
    expect(D2NotificationPolicy.browserPushAvailable, isFalse);
  });

  test('reminder and conversation are not notification candidates', () {
    for (final channel in <D2MessageChannel>[
      D2MessageChannel.reminder,
      D2MessageChannel.companionConversation,
    ]) {
      expect(decision(sample(channel: channel)), D2PreviewResult.wrongChannel);
    }
  });

  test('browser push remains denied even with opt-in and identity', () {
    expect(
      decision(sample(surface: D2NotificationSurface.browserPush)),
      D2PreviewResult.deliveryUnavailable,
    );
    expect(D2NotificationPolicy.browserPushAvailable, isFalse);
  });

  test('missing and cross-patient identity fail closed', () {
    expect(
      decision(sample(authenticatedPatientId: null)),
      D2PreviewResult.patientScopeDenied,
    );
    expect(
      decision(sample(authenticatedPatientId: 0)),
      D2PreviewResult.patientScopeDenied,
    );
    expect(
      decision(sample(recordPatientId: 18)),
      D2PreviewResult.patientScopeDenied,
    );
  });

  test('A to B auth epoch switch and lock invalidate preview', () {
    expect(
      decision(sample(currentAuthEpoch: 10)),
      D2PreviewResult.staleAuthSession,
    );
    expect(decision(sample(isUnlocked: false)), D2PreviewResult.locked);
  });

  test('opt-out, no opt-in and missing verified server consent all deny', () {
    expect(
      decision(sample(globalAiOptOut: true)),
      D2PreviewResult.consentDenied,
    );
    expect(
      decision(sample(explicitProactiveOptIn: false)),
      D2PreviewResult.consentDenied,
    );
    expect(
      decision(sample(serverConsentConfirmed: false)),
      D2PreviewResult.consentDenied,
    );
  });

  test('unknown source, blank proof and wrong version deny', () {
    expect(
      decision(sample(source: D2NotificationSource.unknown)),
      D2PreviewResult.unknownSource,
    );
    expect(
      decision(sample(evidenceId: ' ')),
      D2PreviewResult.unknownSource,
    );
    expect(
      decision(sample(signature: ' ')),
      D2PreviewResult.unknownSource,
    );
    expect(
      decision(sample(sourceVersion: 'unapproved.v1')),
      D2PreviewResult.unknownSource,
    );
  });

  test('emergency authority and treatment changes cannot enter this lane', () {
    expect(
      decision(sample(hasEmergencyAuthority: true)),
      D2PreviewResult.clinicalAuthorityDenied,
    );
    expect(
      decision(sample(suggestsTreatmentChange: true)),
      D2PreviewResult.clinicalAuthorityDenied,
    );
  });

  test('expired, future or illogical evidence windows deny', () {
    expect(
      decision(sample(expiresAt: now)),
      D2PreviewResult.invalidEvidenceWindow,
    );
    expect(
      decision(sample(observedAt: now.add(const Duration(minutes: 1)))),
      D2PreviewResult.invalidEvidenceWindow,
    );
    expect(
      decision(sample(
        observedAt: now.subtract(const Duration(hours: 2)),
        expiresAt: now.subtract(const Duration(hours: 3)),
      )),
      D2PreviewResult.invalidEvidenceWindow,
    );
  });

  test('duplicate and cooldown suppress repeat previews', () {
    expect(
      decision(sample(
        alreadyPreviewedSignatures: const {'approved-source-signature'},
      )),
      D2PreviewResult.duplicate,
    );
    expect(
      decision(sample(lastPreviewAt: now.subtract(const Duration(hours: 23)))),
      D2PreviewResult.cooldown,
    );
    expect(
      decision(sample(lastPreviewAt: now.add(const Duration(minutes: 5)))),
      D2PreviewResult.cooldown,
    );
    expect(
      decision(sample(lastPreviewAt: now.subtract(const Duration(hours: 24)))),
      D2PreviewResult.eligibleForPreviewOnly,
    );
  });
}
