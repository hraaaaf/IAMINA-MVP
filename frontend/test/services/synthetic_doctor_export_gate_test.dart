import 'package:amina/services/synthetic_doctor_export_gate.dart';
import 'package:amina/services/synthetic_doctor_report.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final granted = DateTime.utc(2026, 11, 9, 21);
  final requestTime = DateTime.utc(2026, 11, 10, 10);
  final expiry = DateTime.utc(2026, 11, 10, 11);

  SyntheticDoctorReport fixtureReport() => SyntheticDoctorReport(
    generatedAtUtc: DateTime.utc(2026, 11, 9, 18),
    periodStartUtc: DateTime.utc(2026, 11, 1),
    periodEndUtc: DateTime.utc(2026, 11, 8),
    observations: [
      SyntheticGlucoseObservation(
        recordedAtUtc: DateTime.utc(2026, 11, 2, 8), mgDl: 142,
      ),
      SyntheticGlucoseObservation(
        recordedAtUtc: DateTime.utc(2026, 11, 3, 10), mgDl: null,
      ),
    ],
  );

  SyntheticExportConsentFixture consent({
    SyntheticVaultFixture owner = SyntheticVaultFixture.alpha,
    SyntheticRecipientFixture recipient = SyntheticRecipientFixture.doctorOne,
    DateTime? grantTime,
    DateTime? expiryTime,
    DateTime? revoked,
    bool confirmed = true,
  }) => SyntheticExportConsentFixture(
    owner: owner,
    recipient: recipient,
    purpose: SyntheticExportPurpose.doctorFollowUp,
    grantedAtUtc: grantTime ?? granted,
    expiresAtUtc: expiryTime ?? expiry,
    revokedAtUtc: revoked,
    explicitlyConfirmed: confirmed,
  );

  SyntheticDoctorPreviewIntent intent({
    SyntheticVaultFixture reportOwner = SyntheticVaultFixture.alpha,
    SyntheticVaultFixture activeOwner = SyntheticVaultFixture.alpha,
    SyntheticRecipientFixture recipient = SyntheticRecipientFixture.doctorOne,
    SyntheticRecipientFixture confirmedRecipient =
        SyntheticRecipientFixture.doctorOne,
    DateTime? recipientAt,
    DateTime? requestedAt,
    SyntheticExportConsentFixture? proof,
  }) => SyntheticDoctorPreviewIntent(
    report: fixtureReport(),
    reportOwner: reportOwner,
    activeOwner: activeOwner,
    recipient: recipient,
    confirmedRecipient: confirmedRecipient,
    recipientConfirmedAtUtc: recipientAt ?? DateTime.utc(2026, 11, 10, 9),
    requestedAtUtc: requestedAt ?? requestTime,
    consent: proof ?? consent(),
  );

  test('CAL12 preview only in FR EN AR, no actual patient export', () {
    expect(SyntheticDoctorExportGate.patientExportEnabled, isFalse);
    for (final lang in ['fr', 'en', 'ar']) {
      final text = SyntheticDoctorExportGate.previewHtml(
        intent: intent(), languageCode: lang,
      );
      expect(text, contains('142 mg/dL'));
      expect(text, contains('lang="' + lang + '"'));
      expect(text, isNot(contains('patient_id')));
      expect(text, isNot(contains('<script')));
      expect(text, isNot(contains('https://')));
    }
  });

  test('CAL12 synthetic A to B to A cannot leak other report', () {
    for (final invalid in [
      intent(activeOwner: SyntheticVaultFixture.beta),
      intent(reportOwner: SyntheticVaultFixture.beta),
      intent(
        activeOwner: SyntheticVaultFixture.beta,
        reportOwner: SyntheticVaultFixture.beta,
      ),
      intent(proof: consent(owner: SyntheticVaultFixture.beta)),
    ]) {
      expect(() => SyntheticDoctorExportGate.previewHtml(
        intent: invalid, languageCode: 'fr',
      ), throwsStateError);
    }
    expect(SyntheticDoctorExportGate.previewHtml(
      intent: intent(), languageCode: 'fr',
    ), contains('142 mg/dL'));
  });

  test('CAL12 deny wrong recipient, unconfirmed, revoked or expired', () {
    for (final invalid in [
      intent(recipient: SyntheticRecipientFixture.doctorTwo),
      intent(confirmedRecipient: SyntheticRecipientFixture.doctorTwo),
      intent(proof: consent(confirmed: false)),
      intent(recipientAt: DateTime.utc(2026, 11, 9, 20)),
      intent(recipientAt: DateTime.utc(2026, 11, 10, 11)),
      intent(proof: consent(revoked: DateTime.utc(2026, 11, 10, 9))),
      intent(requestedAt: expiry),
      intent(proof: consent(grantTime: DateTime.utc(2026, 11, 10, 11))),
      intent(proof: consent(expiryTime: DateTime.utc(2026, 11, 9, 20))),
      intent(proof: consent(grantTime: DateTime(2026, 11, 9))),
      intent(requestedAt: DateTime(2026, 11, 10)),
    ]) {
      expect(() => SyntheticDoctorExportGate.previewHtml(
        intent: invalid, languageCode: 'ar',
      ), throwsStateError);
    }
  });
}
