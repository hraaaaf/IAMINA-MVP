// ConsentService — local UI gate for externally processed AI features.
// A Drift timestamp alone is never sufficient: it must be paired with current,
// verified notice evidence held in secure storage. Server egress remains the
// authoritative fail-closed boundary.
import 'dart:async';
import 'package:flutter/foundation.dart';
import '../data/drift/database.dart';

class ConsentService extends ChangeNotifier {
  bool? _hasConsent;
  bool _hasVerifiedEvidence;
  bool _profileHasTimestamp = false;
  bool _hasCompletedOnboarding = false;
  StreamSubscription<PatientProfileData?>? _sub;

  ConsentService({bool hasVerifiedEvidence = false})
    : _hasVerifiedEvidence = hasVerifiedEvidence;

  /// True once the first profile stream event has been processed or seeded.
  bool get isInitialized => _hasConsent != null;

  /// Safe default is false. Both local timestamp and verified evidence required.
  bool get hasConsent => _hasConsent ?? false;

  /// True only when the minimum patient onboarding fields are persisted.
  bool get hasCompletedOnboarding => _hasCompletedOnboarding;

  bool _profileCompletesOnboarding(PatientProfileData? profile) {
    final diabetesType = profile?.diabetesType?.trim();
    final treatment = profile?.treatment?.trim();
    return diabetesType != null &&
        diabetesType.isNotEmpty &&
        treatment != null &&
        treatment.isNotEmpty;
  }

  void _applyProfile(PatientProfileData? profile) {
    final nextCompletedOnboarding = _profileCompletesOnboarding(profile);
    final onboardingChanged =
        nextCompletedOnboarding != _hasCompletedOnboarding;
    _hasCompletedOnboarding = nextCompletedOnboarding;

    _profileHasTimestamp = profile?.aiConsentGivenAt != null;
    final nextConsent = _profileHasTimestamp && _hasVerifiedEvidence;
    final consentChanged = nextConsent != _hasConsent;
    _hasConsent = nextConsent;

    if (onboardingChanged || consentChanged) {
      notifyListeners();
    }
  }

  /// Attach to local profile changes. Legacy timestamps without secure evidence
  /// remain denied after upgrade.
  void attachStream(Stream<PatientProfileData?> profileStream) {
    _sub?.cancel();
    _sub = profileStream.listen(_applyProfile);
  }

  /// Seed synchronously to avoid a redirect flicker on app start.
  void seedInitialProfile(PatientProfileData? profile) {
    _hasCompletedOnboarding = _profileCompletesOnboarding(profile);
    _profileHasTimestamp = profile?.aiConsentGivenAt != null;
    _hasConsent = _profileHasTimestamp && _hasVerifiedEvidence;
  }

  /// Called only after server acceptance, exact response verification, secure
  /// evidence persistence and local timestamp persistence all succeeded.
  void markVerifiedConsent() {
    _hasVerifiedEvidence = true;
    _profileHasTimestamp = true;
    _hasConsent = true;
    _hasDeclinedLocally = false;
    notifyListeners();
  }

  /// Clear the local gate immediately after withdrawal or evidence invalidation.
  void clearVerifiedConsent() {
    _hasVerifiedEvidence = false;
    _profileHasTimestamp = false;
    _hasConsent = false;
    notifyListeners();
  }

  // ── Decline (session-only) ────────────────────────────────────────────────
  bool _hasDeclinedLocally = false;

  bool get hasDeclinedLocally => _hasDeclinedLocally;

  void declineLocally() {
    _hasDeclinedLocally = true;
    notifyListeners();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
