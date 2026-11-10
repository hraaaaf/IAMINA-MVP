import 'dart:typed_data';

import 'package:amina/services/clinical_export_consent_contract.dart';
import 'package:amina/services/clinical_export_ephemeral_draft.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final start = DateTime.utc(2026, 11, 1);
  final end = DateTime.utc(2026, 11, 8);
  final granted = DateTime.utc(2026, 11, 10, 8);
  final now = DateTime.utc(2026, 11, 10, 8, 5);
  final expiry = DateTime.utc(2026, 11, 10, 8, 10);

  DoctorExportConsentDraft consent({
    String owner = 'fixture:vault:a',
    String recipient = 'fixture:doctor:one',
    String locale = 'fr',
    DoctorExportNoticeDraft? claim,
    DoctorExportChannel channel = DoctorExportChannel.localPreview,
    DoctorExportDataCategory category =
        DoctorExportDataCategory.syntheticManualReadings,
    DateTime? periodStart,
    DateTime? periodEnd,
    DateTime? grantedAt,
    DateTime? expiresAt,
    DateTime? confirmedAt,
    DateTime? revoked,
    bool approved = true,
  }) => DoctorExportConsentDraft(
    ownerScope: owner,
    recipientScope: recipient,
    notice: claim ?? DoctorExportDraftNoticeCatalog.forLocale(locale),
    purpose: DoctorExportPurpose.followUpWithClinician,
    channel: channel,
    category: category,
    periodStartUtc: periodStart ?? start,
    periodEndUtc: periodEnd ?? end,
    grantedAtUtc: grantedAt ?? granted,
    expiresAtUtc: expiresAt ?? expiry,
    recipientConfirmedAtUtc: confirmedAt ?? DateTime.utc(2026, 11, 10, 8, 2),
    explicitlyAgreed: approved,
    revokedAtUtc: revoked,
  );

  DoctorExportPreviewRequest request({
    String owner = 'fixture:vault:a',
    String reportOwner = 'fixture:vault:a',
    String recipient = 'fixture:doctor:one',
    String locale = 'fr',
    DoctorExportNoticeDraft? claim,
    DoctorExportChannel channel = DoctorExportChannel.localPreview,
    DoctorExportDataCategory category =
        DoctorExportDataCategory.syntheticManualReadings,
    DateTime? periodStart,
    DateTime? periodEnd,
    DateTime? at,
  }) => DoctorExportPreviewRequest(
    currentOwnerScope: owner,
    reportOwnerScope: reportOwner,
    recipientScope: recipient,
    notice: claim ?? DoctorExportDraftNoticeCatalog.forLocale(locale),
    purpose: DoctorExportPurpose.followUpWithClinician,
    channel: channel,
    category: category,
    periodStartUtc: periodStart ?? start,
    periodEndUtc: periodEnd ?? end,
    nowUtc: at ?? now,
  );

  DoctorExportDenyReason? check({
    DoctorExportPreviewRequest? r,
    DoctorExportConsentDraft? c,
  }) => DoctorExportConsentPolicy.evaluateFixturePreview(
    request: r ?? request(),
    consent: c ?? consent(),
  );

  test('CAL12 distinct medical-export draft, no real patient release', () {
    expect(DoctorExportConsentPolicy.realPatientExportEnabled, isFalse);
    expect(check(), isNull);
    for (final language in ['fr', 'en', 'ar']) {
      final claim = DoctorExportDraftNoticeCatalog.forLocale(language);
      expect(claim.sha256Hex.length, 64);
      expect(claim.version, DoctorExportDraftNoticeCatalog.version);
      expect(check(r: request(locale: language), c: consent(locale: language)),
          isNull);
    }
    expect(
      () => DoctorExportDraftNoticeCatalog.forLocale('ar-MA'),
      throwsArgumentError,
    );
  });

  test('CAL12 denies owner A-B-A mix, forged IDs and different doctor', () {
    expect(
      check(r: request(owner: 'fixture:vault:b')),
      DoctorExportDenyReason.ownerMismatch,
    );
    expect(
      check(r: request(reportOwner: 'fixture:vault:b')),
      DoctorExportDenyReason.ownerMismatch,
    );
    expect(
      check(c: consent(owner: 'fixture:vault:b')),
      DoctorExportDenyReason.ownerMismatch,
    );
    expect(
      check(r: request(owner: 'real-patient-123')),
      DoctorExportDenyReason.nonFixtureIdentity,
    );
    expect(
      check(r: request(recipient: 'dr@hospital.example')),
      DoctorExportDenyReason.nonFixtureIdentity,
    );
    expect(
      check(r: request(recipient: 'fixture:doctor:two')),
      DoctorExportDenyReason.recipientMismatch,
    );
    // B is allowed only as a separately scoped FICTIONAL consent.
    expect(
      check(
        r: request(owner:'fixture:vault:b', reportOwner:'fixture:vault:b'),
        c: consent(owner:'fixture:vault:b'),
      ),
      isNull,
    );
  });

  test('CAL12 rejects change of notice, locale, range and clinical data', () {
    final current = DoctorExportDraftNoticeCatalog.forLocale('fr');
    final stale = DoctorExportNoticeDraft(
      version: 'OLD',
      locale: 'fr',
      sha256Hex: current.sha256Hex,
    );
    final tampered = DoctorExportNoticeDraft(
      version: current.version,
      locale: 'fr',
      sha256Hex: List.filled(64, '0').join(),
    );
    expect(check(c: consent(claim: stale)), DoctorExportDenyReason.noticeChanged);
    expect(check(r: request(claim: tampered)),
        DoctorExportDenyReason.noticeChanged);
    expect(check(r: request(locale:'ar')), DoctorExportDenyReason.noticeChanged);
    expect(
      check(r: request(periodEnd: DateTime.utc(2026, 11, 7))),
      DoctorExportDenyReason.incorrectDataWindow,
    );
    expect(
      check(r: request(periodStart: DateTime.utc(2026, 11, 12))),
      DoctorExportDenyReason.incorrectDataWindow,
    );
    expect(
      check(r: request(category: DoctorExportDataCategory.clinicalMeasurements)),
      DoctorExportDenyReason.unsupportedPurposeOrCategory,
    );
  });

  test('CAL12 preview-only, short consent, UTC and revocation enforcement', () {
    expect(check(r: request(channel: DoctorExportChannel.secureRecipientDelivery)),
        DoctorExportDenyReason.patientExportDisabled);
    expect(check(c: consent(channel: DoctorExportChannel.secureRecipientDelivery)),
        DoctorExportDenyReason.patientExportDisabled);
    expect(check(c: consent(approved:false)),
        DoctorExportDenyReason.consentNotConfirmed);
    expect(check(c: consent(revoked: now)),
        DoctorExportDenyReason.consentRevoked);
    expect(check(c: consent(revoked: DateTime.utc(2026, 11, 11))),
        DoctorExportDenyReason.consentRevoked);
    expect(check(r: request(at: expiry)),
        DoctorExportDenyReason.consentExpiredOrFuture);
    expect(check(c: consent(grantedAt: DateTime.utc(2026, 11, 10, 8, 6))),
        DoctorExportDenyReason.consentExpiredOrFuture);
    expect(check(c: consent(expiresAt: DateTime.utc(2026, 11, 10, 8, 20))),
        DoctorExportDenyReason.consentExpiredOrFuture);
    expect(check(c: consent(confirmedAt: DateTime.utc(2026, 11, 10, 7))),
        DoctorExportDenyReason.destinationConfirmationInvalid);
    expect(check(c: consent(confirmedAt: DateTime.utc(2026, 11, 10, 8, 6))),
        DoctorExportDenyReason.destinationConfirmationInvalid);
    expect(check(r: request(at: DateTime(2026, 11, 10, 8, 5))),
        DoctorExportDenyReason.utcMissing);
    expect(check(c: consent(grantedAt: DateTime(2026, 11, 10, 8))),
        DoctorExportDenyReason.utcMissing);
  });

  test('CAL12 ephemeral payload: defensive copy, success zeroize and no reuse',
      () async {
    final source = Uint8List.fromList([1, 5, 7, 9]);
    final draft = EphemeralClinicalExportDraft.openFixture(
      request: request(), consent: consent(), syntheticBytes: source,
    );
    source[0] = 77;
    Uint8List? borrowed;
    await draft.previewOnce(
      nowUtc: now,
      inspect: (view) async {
        borrowed = view;
        expect(view, orderedEquals([1, 5, 7, 9]));
      },
    );
    expect(draft.isPurged, isTrue);
    expect(borrowed, orderedEquals([0, 0, 0, 0]));
    expect(source[0], 77);
    await expectLater(
      draft.previewOnce(nowUtc: now, inspect: (_) async {}),
      throwsStateError,
    );
  });

  test('CAL12 ephemeral zeroization on error, expiry, cancellation', () async {
    final draft = EphemeralClinicalExportDraft.openFixture(
      request: request(), consent: consent(),
      syntheticBytes: Uint8List.fromList([3, 4, 5]),
    );
    Uint8List? borrowed;
    await expectLater(draft.previewOnce(
      nowUtc: now,
      inspect: (view) async {
        borrowed = view;
        throw StateError('synthetic preview interrupted');
      },
    ), throwsStateError);
    expect(draft.isPurged, isTrue);
    expect(borrowed, orderedEquals([0, 0, 0]));

    final stale = EphemeralClinicalExportDraft.openFixture(
      request: request(), consent: consent(),
      syntheticBytes: Uint8List.fromList([8, 9]),
    );
    await expectLater(
      stale.previewOnce(nowUtc: expiry, inspect: (_) async {}),
      throwsStateError,
    );
    expect(stale.isPurged, isTrue);

    final cancelled = EphemeralClinicalExportDraft.openFixture(
      request: request(), consent: consent(),
      syntheticBytes: Uint8List.fromList([1]),
    );
    cancelled.cancel();
    cancelled.cancel();
    expect(cancelled.isPurged, isTrue);
    await expectLater(
      cancelled.previewOnce(nowUtc: now, inspect: (_) async {}),
      throwsStateError,
    );
  });

  test('CAL12 revoke during await wipes borrowed bytes and fails closed',
      () async {
    final draft = EphemeralClinicalExportDraft.openFixture(
      request: request(), consent: consent(),
      syntheticBytes: Uint8List.fromList([18, 19]),
    );
    Uint8List? borrowed;
    await expectLater(draft.previewOnce(
      nowUtc: now,
      inspect: (view) async {
        borrowed = view;
        draft.revoke();
        await Future<void>.value();
      },
    ), throwsStateError);
    expect(draft.isPurged, isTrue);
    expect(borrowed, orderedEquals([0, 0]));
  });

  test('CAL12 refuses empty/oversized fixture or unapproved data', () {
    expect(
      () => EphemeralClinicalExportDraft.openFixture(
        request: request(), consent: consent(),
        syntheticBytes: Uint8List(0),
      ), throwsArgumentError,
    );
    expect(
      () => EphemeralClinicalExportDraft.openFixture(
        request: request(), consent: consent(),
        syntheticBytes: Uint8List(
          EphemeralClinicalExportDraft.maxSyntheticBytes + 1),
      ), throwsArgumentError,
    );
    expect(
      () => EphemeralClinicalExportDraft.openFixture(
        request: request(
          channel: DoctorExportChannel.secureRecipientDelivery),
        consent: consent(),
        syntheticBytes: Uint8List.fromList([1]),
      ), throwsStateError,
    );
  });
}
